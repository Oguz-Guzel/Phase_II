from Configuration.Generator.Pythia8PowhegEmissionVetoSettings_cfi import *
from Configuration.Generator.MCTunes2017.PythiaCP5Settings_cfi import *
from Configuration.Generator.Pythia8CommonSettings_cfi import *
import FWCore.ParameterSet.Config as cms
import FWCore.ParameterSet.Config as cms                                                                                                                                                  
# link to card:                                                                                                                                                                                             
# https://github.com/cms-sw/genproductions/tree/master/bin/MadGraph5_aMCatNLO/cards/production/2017/13TeV/VBF_HH                                                                                                                                                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                            
externalLHEProducer = cms.EDProducer("ExternalLHEProducer",                                                                                                                                                 
    nEvents = cms.untracked.uint32(5000),                                                                                                                                                                   
    outputFile = cms.string('cmsgrid_final.lhe'),                                                                                                                                                           
    scriptName = cms.FileInPath('GeneratorInterface/LHEInterface/data/run_generic_tarball_cvmfs.sh'),                                                                                                       
    numberOfParameters=cms.uint32(1),
   	args=cms.vstring('/cvmfs/cms.cern.ch/phys_generator/gridpacks/slc6_amd64_gcc630/14TeV/madgraph/V5_2.6.5/VBF_HH_CV_1_C2V_1_C3_1_14TeV/VBF_HH_CV_1_C2V_1_C3_1_14TeV-madgraph_slc6_amd64_gcc630_CMSSW_9_3_16_tarball.tar.xz'),
)


generator = cms.EDFilter("Pythia8HadronizerFilter",
                         maxEventsToPrint=cms.untracked.int32(1),
                         pythiaPylistVerbosity=cms.untracked.int32(1),
                         filterEfficiency=cms.untracked.double(1.0),
                         pythiaHepMCVerbosity=cms.untracked.bool(False),
                         comEnergy=cms.double(14000.),
                         PythiaParameters=cms.PSet(
                             pythia8CommonSettingsBlock,
                             pythia8CP5SettingsBlock,
                             pythia8PowhegEmissionVetoSettingsBlock,
                             processParameters=cms.vstring(

                                 'POWHEG:nFinal = 2',  # Number of final state particles
                                 # (BEFORE THE DECAYS) in the LHE
                                 # other than emitted extra parton
                                 '25:m0 = 125.0',
                                 '25:onMode = off',
                                 '25:onIfMatch = 15 -15',
                                 '25:onIfMatch = 22 22',
                                 'ResonanceDecayFilter:filter = on',
                                 # off: require at least the specified number of daughters, on: require exactly the specified number of daughters
                                 'ResonanceDecayFilter:exclusive = on',
                                 # list of mothers not specified -> count all particles in hard process+resonance decays (better to avoid specifying mothers when including leptons from the lhe in counting, since intermediate resonances are not gauranteed to appear in general
                                 'ResonanceDecayFilter:mothers = 25',
                                 'ResonanceDecayFilter:daughters = 15,15,22,22'

                             ),
                             parameterSets=cms.vstring(
                                 'pythia8CommonSettings',
                                 'pythia8CP5Settings',
                                 'pythia8PowhegEmissionVetoSettings',
                                 'processParameters'
                             )
                             )
)

ProductionFilterSequence = cms.Sequence(generator)
