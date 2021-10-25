import logging
from bamboo.analysisutils import loadPlotIt
import os.path
from bamboo.analysismodules import AnalysisModule, HistogramsModule


class CMSPhase2SimRTBModule(AnalysisModule):
    """ Base module for processing Phase2 flat trees """

    def __init__(self, args):
        super(CMSPhase2SimRTBModule, self).__init__(args)
        self._h_genwcount = {}

    def prepareTree(self, tree, sample=None, sampleCfg=None):
        from bamboo.treedecorators import decorateCMSPhase2SimTree
        from bamboo.dataframebackend import DataframeBackend
        t = decorateCMSPhase2SimTree(tree, isMC=True)
        be, noSel = DataframeBackend.create(t)
        from bamboo.root import gbl
        self._h_genwcount[sample] = be.rootDF.Histo1D(
            gbl.ROOT.RDF.TH1DModel("h_count_genweight",
                                   "genweight sum", 1, 0., 1.),
            "_zero_for_stats",
            "genweight"
        )
        return t, noSel, be, tuple()

    def mergeCounters(self, outF, infileNames, sample=None):
        outF.cd()
        self._h_genwcount[sample].Write("h_count_genweight")

    def readCounters(self, resultsFile):
        return {"sumgenweight": resultsFile.Get("h_count_genweight").GetBinContent(1)}

# BEGIN cutflow reports, adapted from bamboo.analysisutils


logger = logging.getLogger(__name__)

_yieldsTexPreface = "\n".join(f"{ln}" for ln in
                              r"""\documentclass[12pt, landscape]{article}
\usepackage[margin=0.5in]{geometry}
\begin{document}
""".split("\n"))


def _texProcName(procName):
    if ">" in procName:
        procName = procName.replace(">", "$ > $")
    if "=" in procName:
        procName = procName.replace("=", "$ = $")
    if "_" in procName:
        procName = procName.replace("_", "\_")
    return procName


def _makeYieldsTexTable(report, samples, entryPlots, stretch=1.5, orientation="v", align="c", yieldPrecision=1, ratioPrecision=2):
    if orientation not in ("v", "h"):
        raise RuntimeError(
            f"Unsupported table orientation: {orientation} (valid: 'h' and 'v')")
    import plotit.plotit
    from plotit.plotit import Stack
    import numpy as np
    from itertools import repeat, count

    def colEntriesFromCFREntryHists(report, entryHists, precision=1):
        stacks_t = [(entryHists[entries[0]] if len(entries) == 1 else
                     Stack(entries=[entryHists[eName] for eName in entries]))
                    for entries in report.titles.values()]
        return stacks_t, ["& {0:.2e}".format(st_t.contents[1]) for st_t in stacks_t]

    def colEntriesFromCFREntryHists_forEff(report, entryHists, precision=1):
        stacks_t = [(entryHists[entries[0]] if len(entries) == 1 else
                     Stack(entries=[entryHists[eName] for eName in entries]))
                    for entries in report.titles.values()]
        return stacks_t, [" {0} ".format(st_t.contents[1]) for st_t in stacks_t]
    smp_signal = [smp for smp in samples if smp.cfg.type == "SIGNAL"]
    smp_mc = [smp for smp in samples if smp.cfg.type == "MC"]
    smp_data = [smp for smp in samples if smp.cfg.type == "DATA"]
    sepStr_v = "|l|"
    hdrs = ["Selection"]
    entries_smp = [[_texProcName(tName) for tName in report.titles.keys()]]
    stTotMC, stTotData = None, None
    if smp_signal:
        sepStr_v += "|"
        for sigSmp in smp_signal:
            _, colEntries = colEntriesFromCFREntryHists(report,
                                                        {eName: sigSmp.getHist(p) for eName, p in entryPlots.items()}, precision=yieldPrecision)
            sepStr_v += f"{align}|"
            hdrs.append(
                f"{_texProcName(sigSmp.cfg.yields_group)} {sigSmp.cfg.cross_section:f}pb")
            entries_smp.append(colEntries)
    if smp_mc:
        sepStr_v += "|"
        sel_list = []
        for mcSmp in smp_mc:
            _, colEntries = colEntriesFromCFREntryHists(report,
                                                        {eName: mcSmp.getHist(p) for eName, p in entryPlots.items()}, precision=yieldPrecision)
            sepStr_v += f"{align}|"
            if isinstance(mcSmp, plotit.plotit.Group):
                hdrs.append(_texProcName(mcSmp.name))
            else:
                hdrs.append(_texProcName(mcSmp.cfg.yields_group))
            entries_smp.append(_texProcName(colEntries))
            _, colEntries_forEff = colEntriesFromCFREntryHists_forEff(report,
                                                                      {eName: mcSmp.getHist(p) for eName, p in entryPlots.items()}, precision=yieldPrecision)
            colEntries_matrix = np.array(colEntries_forEff)
            sel_eff = np.array([100])
            for i in range(1, len(report.titles)):
                sel_eff = np.append(sel_eff, [float(
                    colEntries_matrix[i]) / float(colEntries_matrix[i-1]) * 100]).tolist()
            for i in range(len(report.titles)):
                sel_eff[i] = str(f"({sel_eff[i]:.2f}\%)")
            entries_smp.append(sel_eff)
            sel_list.append(colEntries_forEff)
    if smp_data:
        sepStr_v += f"|{align}|"
        hdrs.append("Data")
        stTotData, colEntries = colEntriesFromCFREntryHists(report, {eName: Stack(entries=[smp.getHist(
            p) for smp in smp_data]) for eName, p in entryPlots.items()}, precision=yieldPrecision)
        entries_smp.append(colEntries)
    if smp_data and smp_mc:
        sepStr_v += f"|{align}|"
        hdrs.append("Data/MC")
        colEntries = []
        for stData, stMC in zip(stTotData, stTotMC):
            dtCont = stData.contents
            mcCont = stMC.contents
            ratio = np.where(mcCont != 0., dtCont/mcCont,
                             np.zeros(dtCont.shape))
            ratioErr = np.where(mcCont != 0., np.sqrt(
                mcCont**2*stData.sumw2 + dtCont**2*(stMC.sumw2+stMC.syst2))/mcCont**2, np.zeros(dtCont.shape))
            colEntries.append("${{0:.{0}f}} \pm {{1:.{0}f}}$".format(
                ratioPrecision).format(ratio[1], ratioErr[1]))
        entries_smp.append(colEntries)
    if len(colEntries) < 2:
        logger.warning("No samples, so no yields.tex")
    return "\n".join(([
        f"\\begin{{tabular}}{{ {sepStr_v} }}",
        "    \\hline",
        "    {0} \\\\".format(" & ".join(hdrs)),
        "    \\hline"]+[
            "    {0} \\\\".format(
                " ".join(smpEntries[i] for smpEntries in entries_smp))
            for i in range(len(report.titles))])+[
        "    \\hline",
        "\\end{tabular}",
        "\\end{document}"
    ])


def printCutFlowReports(config, reportList, workdir=".", resultsdir=".", readCounters=lambda f: -1., eras=("all", None), verbose=False):
    """
    Print yields to the log file, and write a LaTeX yields table for each
    Samples can be grouped (only for the LaTeX table) by specifying the
    ``yields-group`` key (overriding the regular ``groups`` used for plots).
    The sample (or group) name to use in this table should be specified
    through the ``yields-title`` sample key.
    In addition, the following options in the ``plotIt`` section of
    the YAML configuration file influence the layout of the LaTeX yields table:
    - ``yields-table-stretch``: ``\\arraystretch`` value, 1.15 by default
    - ``yields-table-align``: orientation, ``h`` (default), samples in rows, or ``v``, samples in columns
    - ``yields-table-text-align``: alignment of text in table cells (default: ``c``)
    - ``yields-table-numerical-precision-yields``: number of digits after the decimal point for yields (default: 1)
    - ``yields-table-numerical-precision-ratio``: number of digits after the decimal point for ratios (default: 2)
    """
    eraMode, eras = eras
    if not eras:  # from config if not specified
        eras = list(config["eras"].keys())
    # helper: print one bamboo.plots.CutFlowReport.Entry

    def printEntry(entry, printFun=logger.info, recursive=True, genEvents=None):
        effMsg = ""
        if entry.parent:
            sumPass = entry.nominal.GetBinContent(1)
            sumTotal = entry.parent.nominal.GetBinContent(1)
            if sumTotal != 0.:
                effMsg = f", Eff={sumPass/sumTotal:.2%}"
                if genEvents:
                    effMsg += f", TotalEff={sumPass/genEvents:.2%}"
        printFun(
            f"Selection {entry.name}: N={entry.nominal.GetEntries()}, SumW={entry.nominal.GetBinContent(1)}{effMsg}")
        if recursive:
            for c in entry.children:
                printEntry(c, printFun=printFun,
                           recursive=recursive, genEvents=genEvents)
    # retrieve results files, get generated events for each sample
    from bamboo.root import gbl
    resultsFiles = dict()
    generated_events = dict()
    for smp, smpCfg in config["samples"].items():
        if "era" not in smpCfg or smpCfg["era"] in eras:
            resF = gbl.TFile.Open(os.path.join(resultsdir, f"{smp}.root"))
            resultsFiles[smp] = resF
            genEvts = None
            if "generated-events" in smpCfg:
                if isinstance(smpCfg["generated-events"], str):
                    genEvts = readCounters(resF)[smpCfg["generated-events"]]
                else:
                    genEvts = smpCfg["generated-events"]
            generated_events[smp] = genEvts
    has_plotit = None
    try:
        import plotit.plotit
        has_plotit = True
    except ImportError:
        has_plotit = False
    from bamboo.plots import EquidistantBinning as EqB

    class YieldPlot:
        def __init__(self, name):
            self.name = name
            self.plotopts = dict()
            self.axisTitles = ("Yield",)
            self.binnings = [EqB(1, 0., 1.)]
    for report in reportList:
        smpReports = {smp: report.readFromResults(
            resF) for smp, resF in resultsFiles.items()}
        # debug print
        for smp, smpRep in smpReports.items():
            if smpRep.printInLog:
                logger.info(f"Cutflow report {report.name} for sample {smp}")
                for root in smpRep.rootEntries():
                    printEntry(root, genEvents=generated_events[smp])
        # save yields.tex (if needed)
        if any(len(cb) > 1 or tt != cb[0] for tt, cb in report.titles.items()):
            if not has_plotit:
                logger.error(
                    f"Could not load plotit python library, no TeX yields tables for {report.name}")
            else:
                yield_plots = [YieldPlot(f"{report.name}_{eName}")
                               for tEntries in report.titles.values() for eName in tEntries]
                out_eras = []
                if len(eras) > 1 and eraMode in ("all", "combined"):
                    out_eras.append((f"{report.name}.tex", eras))
                if len(eras) == 1 or eraMode in ("split", "all"):
                    for era in eras:
                        out_eras.append((f"{report.name}_{era}.tex", [era]))
                for outName, iEras in out_eras:
                    pConfig, samples, plots, _, _ = loadPlotIt(
                        config, yield_plots, eras=iEras, workdir=workdir, resultsdir=resultsdir, readCounters=readCounters)
                    tabBlock = _makeYieldsTexTable(report, samples,
                                                   {p.name[len(
                                                       report.name)+1:]: p for p in plots},
                                                   stretch=pConfig.yields_table_stretch,
                                                   orientation=pConfig.yields_table_align,
                                                   align=pConfig.yields_table_text_align,
                                                   yieldPrecision=pConfig.yields_table_numerical_precision_yields,
                                                   ratioPrecision=pConfig.yields_table_numerical_precision_ratio)
                    with open(os.path.join(workdir, outName), "w") as ytf:
                        ytf.write("\n".join((_yieldsTexPreface, tabBlock)))
                    logger.info("Yields table for era(s) {0} was written to {1}".format(
                        ",".join(eras), os.path.join(workdir, outName)))

# END cutflow reports, adapted from bamboo.analysisutils


class CMSPhase2SimHistoModule(CMSPhase2SimRTBModule, HistogramsModule):
    """ Base module for producing plots from Phase2 flat trees """

    def __init__(self, args):
        super(CMSPhase2SimHistoModule, self).__init__(args)

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        """ Customised cutflow reports and plots """
        if not self.plotList:
            self.plotList = self.getPlotList(resultsdir=resultsdir)
        from bamboo.plots import Plot, DerivedPlot, CutFlowReport
        plotList_cutflowreport = [
            ap for ap in self.plotList if isinstance(ap, CutFlowReport)]
        plotList_plotIt = [ap for ap in self.plotList if (isinstance(
            ap, Plot) or isinstance(ap, DerivedPlot)) and len(ap.binnings) == 1]
        eraMode, eras = self.args.eras
        if eras is None:
            eras = list(config["eras"].keys())
        if plotList_cutflowreport:
            printCutFlowReports(config, plotList_cutflowreport, workdir=workdir, resultsdir=resultsdir,
                                readCounters=self.readCounters, eras=(eraMode, eras), verbose=self.args.verbose)
        if plotList_plotIt:
            from bamboo.analysisutils import writePlotIt, runPlotIt
            cfgName = os.path.join(workdir, "plots.yml")
            writePlotIt(config, plotList_plotIt, cfgName, eras=eras, workdir=workdir, resultsdir=resultsdir,
                        readCounters=self.readCounters, vetoFileAttributes=self.__class__.CustomSampleAttributes, plotDefaults=self.plotDefaults)
            runPlotIt(cfgName, workdir=workdir, plotIt=self.args.plotIt,
                      eras=(eraMode, eras), verbose=self.args.verbose)

################################
  ## Actual analysis module ##
################################


class CMSPhase2Sim(CMSPhase2SimHistoModule):
    def definePlots(self, t, noSel, sample=None, sampleCfg=None):
        from bamboo.plots import Plot, CutFlowReport
        from bamboo.plots import EquidistantBinning as EqB
        from bamboo import treefunctions as op

        # count no of events here

        noSel = noSel.refine("withgenweight", weight=t.genweight)

        plots = []

        # select photons
        photons = op.select(t.gamma, lambda ph: op.AND(op.abs(ph.eta) < 3, op.NOT(
            op.in_range(1.442, op.abs(ph.eta), 1.566)), ph.pt > 25))

        # selection of loose ID photon
        looseIDPhotons = op.select(photons, lambda ph: ph.idpass & (1 << 0))

        # sortIDphotons
        sortedIDphotons = op.sort(looseIDPhotons, lambda ph: -ph.pt)

        mgg = op.invariant_mass(sortedIDphotons[0].p4, sortedIDphotons[1].p4)

        # selection: at least 2 photons with invariant mass within [100,150]
        twoPhotonsSel = noSel.refine(
            "hasInvMassPhPh", cut=op.rng_len(sortedIDphotons) >= 2)

        # pT/InvM(gg) > 0.33 selection for leading photon
        pTmggRatioLeading_sel = twoPhotonsSel.refine(
            "ptMggLeading", cut=op.product(sortedIDphotons[0].pt, op.pow(mgg, -1)) > 0.33)
        pTmggRatio_sel = pTmggRatioLeading_sel.refine(
            "ptMggLead_Subleading", cut=op.product(sortedIDphotons[1].pt, op.pow(mgg, -1)) > 0.25)
        mgg_sel = pTmggRatio_sel.refine("mgg_sel", cut=[mgg > 100])

        # electrons

        electrons = op.select(t.elec, lambda el: op.AND(op.abs(el.eta) < 3, op.NOT(
            op.in_range(1.442, op.abs(el.eta), 1.566)), el.pt > 10.))

        IDelectrons = op.select(
            electrons, lambda el: el.idpass & (1 << 0))  # loose ID

        cleanedElectrons = op.select(IDelectrons, lambda el: op.NOT(
            op.rng_any(sortedIDphotons, lambda ph: op.deltaR(el.p4, ph.p4) < 0.2)))

        # muons

        muons = op.select(t.muon, lambda mu: op.AND(
            mu.pt > 10., op.abs(mu.eta) < 3))

        isolatedMuons = op.select(muons, lambda mu: mu.isopass & (1 << 2))

        IDmuons = op.select(
            isolatedMuons, lambda mu: mu.idpass & (1 << 0))  # loose ID

        cleanedMuons = op.select(IDmuons, lambda mu: op.NOT(
            op.rng_any(sortedIDphotons, lambda ph: op.deltaR(mu.p4, ph.p4) < 0.2)))

        # taus

        taus = op.select(t.tau, lambda tau: op.AND(
            tau.pt > 20., op.abs(tau.eta) < 3))

        isolatedTaus = op.select(taus, lambda tau: tau.isopass & (1 << 2))

        cleanedTaus = op.select(isolatedTaus, lambda tau: op.AND(
            op.NOT(op.rng_any(sortedIDphotons,
                   lambda ph: op.deltaR(tau.p4, ph.p4) < 0.2)),
            op.NOT(op.rng_any(cleanedElectrons,
                   lambda el: op.deltaR(tau.p4, el.p4) < 0.2)),
            op.NOT(op.rng_any(cleanedMuons,
                   lambda mu: op.deltaR(tau.p4, mu.p4) < 0.2))
        ))

        def nDaughters(gen):
            """Return the number of daughters of a given object. """
            return gen.d2() - gen.d1()
        
        genTaus = op.select(t.genpart, lambda g: op.abs(g.pid) == 15)
        
        def nDaughters(gen):
            """Returns the number of daughters of a genparticle. """
            return gen.d2() - gen.d1()
        
        oneGenTauSel = noSel.refine("onegentau", cut = [op.rng_len(genTaus) >= 1])
        

        # jets

        jets = op.select(t.jetpuppi, lambda jet: op.AND(
            jet.pt > 30., op.abs(jet.eta) < 3))

        IDJets = op.select(jets, lambda j: j.idpass & (1 << 2))  # tight ID

        cleanedJets = op.select(IDJets, lambda j: op.AND(
            op.NOT(op.rng_any(cleanedElectrons,
                   lambda el: op.deltaR(j.p4, el.p4) < 0.4)),
            op.NOT(op.rng_any(cleanedMuons, lambda mu: op.deltaR(j.p4, mu.p4) < 0.4)),
            op.NOT(op.rng_any(cleanedTaus, lambda tau: op.deltaR(j.p4, tau.p4) < 0.4)),
            op.NOT(op.rng_any(sortedIDphotons,
                   lambda ph: op.deltaR(j.p4, ph.p4) < 0.2))
        ))

        btaggedJets = op.select(
            cleanedJets, lambda j: j.btag & (1 << 1))  # medium  WP

        # mJets = op.invariant_mass(cleanedJets[0].p4, cleanedJets[1].p4)
        # hJets = op.sum(cleanedJets[0].p4, cleanedJets[1].p4)

        # met = op.select(t.metpuppi)

      # selections

        # sel1 = noSel.refine("DiPhoton", cut=op.AND(
        # (op.rng_len(looseIDPhotons) >= 2), (looseIDPhotons[0].pt > 35.)))

        TwoTaus_sel = mgg_sel.refine(
            "TwoPhTwoTau", cut=op.rng_len(cleanedTaus) >= 2)

        OneJetSel = TwoTaus_sel.refine(
            "twojetsel", cut=op.rng_len(cleanedJets) >= 1)

        btaggedJetSel = OneJetSel.refine(
            "btaggedjet", cut=op.rng_len(btaggedJets) >= 1)

       # plots

        plots.append(Plot.make1D("LeadingPhotonPTtwoPhotonsSel", sortedIDphotons[0].pt, twoPhotonsSel, EqB(
            30, 0., 250.), title="Leading Photon pT"))

        plots.append(Plot.make1D("LeadingPhotonPTpTmggRatio_sel", sortedIDphotons[0].pt, mgg_sel, EqB(
            30, 0., 250.), title="Leading Photon pT"))

        plots.append(Plot.make1D("leadingTau_pt", cleanedTaus[0].pt, TwoTaus_sel, EqB(
            30, 0., 250.), title="Leading Tau p_{T}"))

        plots.append(Plot.make1D("leadingjet_pt", cleanedJets[0].pt, OneJetSel, EqB(
            30, 0., 250.), title="Leading Jet p_{T}"))

        plots.append(Plot.make1D("leadingbtaggedjet_pt", btaggedJets[0].pt, btaggedJetSel, EqB(
            30, 0., 250.), title="Leading Btagged Jet p_{T}"))
        
        plots.append(Plot.make1D("gentau_pt", genTaus[0].pt, oneGenTauSel, EqB(
            30, 0., 250.), title="Leading Gen Tau p_{T}"))

        return plots
