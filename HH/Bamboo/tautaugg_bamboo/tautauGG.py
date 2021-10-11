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
                gbl.ROOT.RDF.TH1DModel("h_count_genweight", "genweight sum", 1, 0., 1.),
                "_zero_for_stats",
                "genweight"
                )
        return t, noSel, be, tuple()
    def mergeCounters(self, outF, infileNames, sample=None):
        outF.cd()
        self._h_genwcount[sample].Write("h_count_genweight")
    def readCounters(self, resultsFile):
        return {"sumgenweight": resultsFile.Get("h_count_genweight").GetBinContent(1)}

class CMSPhase2SimRTBHistoModule(CMSPhase2SimRTBModule, HistogramsModule):
    """ Base module for producing plots from Phase2 flat trees """
    def __init__(self, args):
        super(CMSPhase2SimRTBHistoModule, self).__init__(args)


################################
## An analysis module example ##
################################

class CMSPhase2SimTest(CMSPhase2SimRTBHistoModule):
    def definePlots(self, t, noSel, sample=None, sampleCfg=None):
        from bamboo.plots import Plot, CutFlowReport
        from bamboo.plots import EquidistantBinning as EqB
        from bamboo import treefunctions as op
        
        #count no of events here 

        noSel = noSel.refine("withgenweight", weight=t.genweight)

        plots = []

        #H->gg 

        #selection of photons with eta in the detector acceptance
        photons = op.select(t.gamma, lambda ph : op.AND(op.abs(ph.eta) < 3, ph.pt > 25.)) 
        #selection of photons with loose ID        
        cleanedPhotons = op.select(photons, lambda ph : ph.idpass & ( 1<<0 ))
 
        #sort photons by pT 
        sort_ph = op.sort(photons, lambda ph : -ph.pt)

        #sortcleanphotons
        sorted_ph = op.sort(cleanedPhotons, lambda ph : -ph.pt)

        #selection: 2 photons (at least) in an event with invariant mass within [100,150]
        hasTwoPh = noSel.refine("hasMassPhPh", cut= op.AND(
           (op.rng_len(sort_ph) >= 2), 
           (op.in_range(100, op.invariant_mass(sort_ph[0].p4, sort_ph[1].p4), 180)) 
           ))

        mGG = op.invariant_mass(sorted_ph[0].p4, sorted_ph[1].p4)
        hGG = op.sum(sorted_ph[0].p4, sorted_ph[1].p4)

       #H->WW->2q1l1nu
       
        electrons = op.select(t.elec, lambda el : op.AND(
        el.pt > 10., op.abs(el.eta) < 3
        ))
        
        muons = op.select(t.muon, lambda mu : op.AND(
        mu.pt > 10., op.abs(mu.eta) < 3
        ))

        taus = op.select(t.tau, lambda ta : op.AND(
        ta.pt > 20., op.abs(ta.eta) < 3
        ))
        
        identifiedElectrons = op.select(electrons, lambda el : el.idpass & (1<<0) )  # loose ID  
        cleanedElectrons = op.select(identifiedElectrons, lambda el : op.NOT(op.rng_any(photons, lambda ph : op.deltaR(el.p4, ph.p4) < 0.4))) # dR  
        
        isolatedMuons = op.select(muons, lambda mu : mu.isopass & (1<<2) ) # tight ID & ISO
        identifiedMuons = op.select(isolatedMuons, lambda mu : mu.idpass & (1<<2) ) 
        cleanedMuons = op.select(identifiedMuons, lambda mu : op.NOT(op.rng_any(photons, lambda ph : op.deltaR(mu.p4, ph.p4) < 0.4 )))
    
        isolatedTaus = op.select(taus, lambda ta : ta.isopass & (1<<2) )
        cleanedTaus = op.select(isolatedTaus, lambda ta : op.NOT(op.rng_any(photons, lambda ph : op.deltaR(ta.p4, ph.p4) < 0.4 )))
          
        #select jets with pt>25 GeV end eta in the detector acceptance
        jets = op.select(t.jetpuppi, lambda jet : op.AND(jet.pt > 30., op.abs(jet.eta) < 2.5))
        
        identifiedJets = op.select(jets, lambda j : j.idpass & (1<<2))
        cleanedJets = op.select(identifiedJets, lambda j : op.AND(
        op.NOT(op.rng_any(identifiedElectrons, lambda el : op.deltaR(el.p4, j.p4) < 0.4) ),   #identified or cleaned mu/e ? 
        op.NOT(op.rng_any(identifiedMuons, lambda mu : op.deltaR(mu.p4, j.p4) < 0.4) )
        ))
         
        mJets= op.invariant_mass(cleanedJets[0].p4, cleanedJets[1].p4)
        hJets = op.sum(cleanedJets[0].p4, cleanedJets[1].p4)
       
        met = op.select(t.metpuppi)
 
      #selections

        sel1 = noSel.refine("DiPhoton", cut = op.AND((op.rng_len(sorted_ph) >= 2), (sorted_ph[0].pt > 35.)))
        
        sel2 = sel1.refine("TwoPhTwoTau", cut = op.rng_len(cleanedTaus) >= 1)
     
       #plots
       
       #sel1
        plots.append(Plot.make1D("LeadingPhotonPTSel1", sort_ph[0].pt, sel1, EqB(30, 0., 250.), title="Leading Photon pT"))
            
        plots.append(Plot.make1D("SubLeadingPhotonPTSel1", sort_ph[1].pt, sel1, EqB(30, 0., 250.), title="SubLeading Photon pT"))
       
       #sel2 
        
        plots.append(Plot.make1D("LeadingPhotonPTSel2", sorted_ph[0].pt, sel2, EqB(30, 0., 250.), title="Leading Photon pT"))
            
        plots.append(Plot.make1D("SubLeadingPhotonPTSel2", sorted_ph[1].pt, sel2, EqB(30, 0., 250.), title="SubLeading Photon pT")) 
          

       #diphoton invariant mass

        plots.append(Plot.make1D("Inv_mass_ggSel1", mGG, sel1, EqB(50, 100.,150.), title = "m_{\gamma\gamma}"))
        plots.append(Plot.make1D("Inv_mass_ggSel2", mGG, sel2, EqB(50, 100.,150.), title = "m_{\gamma\gamma}"))


       #yields
        # yields = CutFlowReport("yields", recursive=True, printInLog=True)
        # plots.append(yields)
        # yields.add(noSel, title= 'noSel')
        # yields.add(sel1, title='sel1')
        # yields.add(sel2, title='sel2')

        return plots
