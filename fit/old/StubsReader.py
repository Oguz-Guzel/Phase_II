#!/usr/bin/env python

import os
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
import ROOT
import math
from ROOT import TFile, TH1, TCanvas, TGraph, TH1F, THStack, TF1 
from ROOT import TLegend, TApplication, TRatioPlot, TPad
from array import array
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('data', help='Stubs/L1? ')
args = parser.parse_args()
data = args.data

def histoStyle(h1) :
  h1.SetMinimum(1e-08)
  h1.SetMaximum(1e-04)
  h1.SetLineColor(2)
  h1.SetLineWidth(3)
  h1.SetMarkerColor(2)
  h1.SetMarkerStyle(20)
  h1.GetXaxis().SetTitle( 'LET' )
  h1.GetYaxis().SetTitle( '#sigma' )
  h1.SetStats(0)
  return h1

def func(x,par):
  #print ("In Function:", x,par[0], par[1], par[2], par[3] )
  if par[2]!=0:
    y = par[0]*(1-math.exp(-((x - par[1])/par[2])**par[3]))
  else:
    y = 0  
  return y


def SEU_xsec(par):
  sigmas = []
  probb = []

  for index, row in prob.iterrows():
    sigmas.append(func(row['Energy Deposited (MeV)'], par))
    probb.append(row['Probability (cm2/bit)'])

  SEU_xs=0
  for i in range(len(sigmas)):
    #print(sigmas[i], probb[i])
    if i <len(probb)-1:
      SEU_xs += (sigmas[i+1]-sigmas[i])*probb[i-1]*1e+08

  return SEU_xs     
      

h1 = TH1F ("h1","Histogram",100,0,50)
h2 = TH1F ("h2","Histogram",100,0,50)
h3 = TH1F ("h3","Histogram",100,0,50)
h4 = TH1F ("h4","Histogram",100,0,50)

if data == 'L1':
  ifL1  = True
  rowID    = 'L1'
else:
  ifL1  = False
  rowID    = 'Stubs'  



data = pd.read_csv('l1.csv', usecols=('Name','Rate (kHz)','Ion','L1', 'LET','Flux','Stubs'))
prob = pd.read_csv('SEU_rate_LHC_Tracker.csv', usecols=('Probability (cm2/bit)','Energy Deposited (MeV)'))

c1 = TCanvas( 'c1', '', 200, 10, 700, 500 )
c2 = TCanvas( 'c2', '', 200, 10, 700, 500 )

c1.SetFillColor( 0 )
c1.SetGrid()
c1.SetLogy(1)

c2.SetFillColor( 0 )
c2.SetGrid()
c2.SetLogy(1)

titles= []
names = []

print "\n\n"
print "######################################################"
print "################### Reading",rowID,"data ###############"
print "######################################################"
print "\n\n"
#h3.SetBinContent(h3.FindBin(2),1.11e-06)
#h3.SetBinError(h3.FindBin(2),1e-07)
#h3.SetBinContent(h3.FindBin(5),3.47e-06)
#h3.SetBinError(h3.FindBin(5),1e-07)

for index, row in data.iterrows():
    if row['Rate (kHz)']==500 and row['Name']== 'MPA' and row['Ion']!= 'Ne 30' :
      
        y = row[rowID]/(row['Flux']*300)
        erry = y*(1/math.sqrt(row[rowID]+1.0/math.sqrt(row['Flux']*300)))

        h1.SetBinContent(h1.FindBin(row['LET']), y)
        h1.SetBinError(h1.FindBin(row['LET']), erry)
        if index == 0 :
            #print(index)
            titles.append(str(rowID+": "+row['Name']+", "+str(row['Rate (kHz)'])+" kHz"))
            names.append(str(rowID+row['Name']+str(row['Rate (kHz)'])))
        #print(row['Name'], row['Rate (kHz)'], row['LET'], row[rowID], index)
    if row['Rate (kHz)']==10 and row['Name']== 'MPA' and row['Ion']!= 'Ne 30' :
        y = row[rowID]/(row['Flux']*300)
        erry = y*(1/math.sqrt(row[rowID]+1.0/math.sqrt(row['Flux']*300)))
        h2.SetBinContent(h2.FindBin(row['LET']), y)
        h2.SetBinError(h2.FindBin(row['LET']), erry)
        if index == 8:
            #print(index)
            titles.append(str(rowID+": "+row['Name']+", "+str(row['Rate (kHz)'])+" kHz"))
            names.append(str(rowID+row['Name']+str(row['Rate (kHz)'])))
        #print(row['Name'], row['Rate (kHz)'], row['LET'], row[rowID])
    if row['Rate (kHz)']==750 and row['Name']== 'CBC' and row['Ion']!= 'Ne 30' :
        y = row[rowID]/(row['Flux']*300)
        erry = y*(1/math.sqrt(row[rowID]+1.0/math.sqrt(row['Flux']*300)))
        #print y, erry
        h3.SetBinContent(h3.FindBin(row['LET']), y)
        h3.SetBinError(h3.FindBin(row['LET']), erry)
        if index == 15:
            titles.append(str(rowID+": "+row['Name']+", "+str(row['Rate (kHz)'])+" kHz"))
            names.append(str(rowID+row['Name']+str(row['Rate (kHz)'])))
        #print(row['Name'], row['Rate (kHz)'], row['LET'], row[rowID])
    if row['Rate (kHz)']==10 and row['Name']== 'CBC' and row['Ion']!= 'Ne 30' :
        y = row[rowID]/(row['Flux']*300)
        erry = y*(1/math.sqrt(row[rowID]+1.0/math.sqrt(row['Flux']*300)))
        h4.SetBinContent(h4.FindBin(row['LET']), y)
        h4.SetBinError(h4.FindBin(row['LET']), erry)
        if index == 23:
            titles.append(str(rowID+": "+row['Name']+", "+str(row['Rate (kHz)'])+" kHz"))
            names.append(str(rowID+row['Name']+str(row['Rate (kHz)'])))
        #print(row['Name'], row['Rate (kHz)'], row['LET'], row[rowID])

fit1 = TF1('fit1', "[0]*(1-exp(-((x*0.232-[1])/[2])**[3]))", -0.0001 ,50.)
fit1.SetParNames("sigma0","E0","W", "s")
parnames = ["sigma0","E0","W", "s"]


histoStyle(h1)
histoStyle(h2)
histoStyle(h3)
histoStyle(h4)


c2.cd()
h1.SetLineColor(2)
h1.SetMarkerColor(2)
h2.SetLineColor(3)
h2.SetMarkerColor(3)
h2.SetMarkerStyle(22)
h3.SetLineColor(1)
h3.SetMarkerColor(1)
h4.SetLineColor(4)
h4.SetMarkerColor(4)
h4.SetMarkerStyle(22)
h1.SetTitle(rowID)
h2.SetTitle(rowID)
h3.SetTitle(rowID)
h4.SetTitle(rowID)
h1.Draw('P')
h2.Draw('P,sames')
h3.Draw('P,sames')
h4.Draw('P,sames')
legend = TLegend (0.61,0.11,0.88,0.33);
#legend.SetHeader("The Legend Title","C"); // option "C" allows to center the header
legend.AddEntry(h1,names[0],"lp");
legend.AddEntry(h2,names[1],"lp");
legend.AddEntry(h3,names[2],"lp");
legend.AddEntry(h4,names[3],"lp");
legend.Draw();
c2.SaveAs(rowID+".pdf")
c2.SaveAs(rowID+".png")
#c2.SaveAs(rowID+".C")


histoStyle(h1)
histoStyle(h2)
histoStyle(h3)
histoStyle(h4)


c1.cd()
c1.Update()
h1.SetTitle(titles[0])

if ifL1:
  fit1.SetParameter(0, 1.5e-05)
  #fit1.SetParLimits(0,1e-05,1e-04 );
  fit1.SetParameter(1,0.00001 ) #0.24
  fit1.SetParLimits(1,1e-08,5e-05)
  #fit1.SetStepSize(1,1e-08)
  #fit1.SetParLimits(1,0,1) 
  fit1.SetParameter(2, 15) #2
  #fit1.SetParLimits(2, 0,100 )
  fit1.SetParameter(3, 1 )#1
  #fit1.SetParLimits(3, 0, 1.5)
else:
  fit1.SetParameter(0, 1.5e-05)
  #fit1.SetParLimits(0,1e-05,5e-05 );
  fit1.SetParameter(1,0.00001 ) #0.24
  fit1.SetParLimits(1,1e-07,5e-05)
  #fit1.SetStepSize(1,1e-08)
  #fit1.SetParLimits(1,0,1) 
  fit1.SetParameter(2, 15) #2
  #fit1.SetParLimits(2, 0,100 )
  fit1.SetParameter(3, 0.5 )#1
  #fit1.SetParLimits(3, 0, 2)


h1.Fit(fit1, 'R')
c1.SaveAs(names[0]+".pdf")
c1.SaveAs(names[0]+".png")
#c1.SaveAs(names[0]+".C")

parMPA=[]
parerrMPA=[]
for i in range(fit1.GetNpar()):
  parMPA.append(fit1.GetParameter(i))
  parerrMPA.append(fit1.GetParError(i))



c1.Update()
h3.SetTitle(titles[2])
if ifL1: 
  fit1.SetParameter(0, 1.30596e-05)
  #fit1.SetParLimits(0,1e-05,1e-02);
  fit1.SetParameter(1,0.00001 ) #0.24
  fit1.SetParLimits(1,1e-08,5e-05)
  #fit1.SetStepSize(1,1e-08)
  #fit1.SetParLimits(1,0,1) 
  fit1.SetParameter(2, 15) #2
  #fit1.SetParLimits(2, 0,100 )
  fit1.SetParameter(3, 1 )
  #fit1.SetParLimits(3, 0, 2)
  #
else:
  fit1.SetParameter(0, 1.30596e-05)
  ##fit1.SetParLimits(0,1e-05,9e-05 );
  fit1.SetParameter(1,0.00001 ) #0.24
  fit1.SetParLimits(1,1e-07,5e-05)
  #fit1.SetStepSize(1,1e-08)
  #fit1.SetParLimits(1,0,1) 
  fit1.SetParameter(2, 15) #2
  #fit1.SetParLimits(2, 0,100 )
  fit1.SetParameter(3, 1 )#1
  fit1.SetParLimits(3, 0, 2)

h3.Fit(fit1, 'R')
#chk.NormalizeErrors()
c1.SaveAs(names[2]+".pdf")
c1.SaveAs(names[2]+".png")
#c1.SaveAs(names[2]+".C")



#c1.Update()
#h2.SetTitle(titles[1])
#fit1.SetParameter(0,0.000001)
#fit1.SetParameter(1,0)
#fit1.SetParameter(2,10)
#fit1.SetParameter(3,1)
#h2.Fit(fit1, 'R')
#c1.SaveAs(names[1]+".pdf")
#c1.SaveAs(names[1]+".png")
#c1.SaveAs(names[1]+".C")
#
#
#

#c1.Update()
#h4.SetTitle(titles[3])
#h4.Draw('P')
#fit1.SetParameter(0,0.000001)
#fit1.SetParameter(1,0)
#fit1.SetParameter(2,10)
#fit1.SetParameter(3,1)
#h4.Fit(fit1, 'R')
#c1.SaveAs(names[3]+".pdf")
#c1.SaveAs(names[3]+".png")
#c1.SaveAs(names[3]+".C")




parCBC=[]
parerrCBC=[]
for i in range(fit1.GetNpar()):
  parCBC.append(fit1.GetParameter(i))
  parerrCBC.append(fit1.GetParError(i))



print "\n\n"
print "######################################################"
print "################### MPA, 500 kHz, 200 PU #############"
print "######################################################"
print "\n\n"

for i in range(len(parMPA)):
  print parnames[i],":", "{:0.2e}".format(parMPA[i]), "+-", "{:0.2e}".format(parerrMPA[i])

print "SEU xs for MPA case: ", "{:0.2e}".format(SEU_xsec(parMPA)), " error rate:", "{:0.2e}".format(SEU_xsec(parMPA)*1.6e+07)



print "\n\n"
print "######################################################"
print "################### CBC, 750 kHz, 250 PU #############"
print "######################################################"
print "\n\n"

for i in range(len(parCBC)):
  print parnames[i],":", "{:0.2e}".format(parCBC[i]), "+-", "{:0.2e}".format(parerrCBC[i])
  
#print(func(2*0.232, par))
#print(func(5*0.232, par))


print "SEU xs for CBC case: ", "{:0.2e}".format(SEU_xsec(parCBC)), " error rate:", "{:0.2e}".format(SEU_xsec(parCBC)*1.6e+07)
print "\n\n"




#os.system("mv *.pdf *.png ~/cernbox/www/Detectors/Upgrade/CIC/")

