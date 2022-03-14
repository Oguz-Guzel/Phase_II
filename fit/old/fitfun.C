#include  <iostream>
#include "TLegend.h"
#include "TH1F.h"
#include "TGraphErrors.h"
#include "TF1.h"
#include "TMath.h"


Double_t CrystalBall(Double_t *x,Double_t *par) {

  Double_t t = (x[0]-par[2])/par[3];
  if (par[0] < 0) t = -t;

  Double_t absAlpha = fabs((Double_t)par[0]);

  if (t >= -absAlpha) {
    return par[4]*exp(-0.5*t*t);
  }
  else {
    Double_t a =  TMath::Power(par[1]/absAlpha,par[1])*exp(-0.5*absAlpha*absAlpha);
    Double_t b= par[1]/absAlpha - absAlpha;

    return par[4]*(a/TMath::Power(b - t, par[1]));
  }
}


Double_t invlandauGaus(Double_t *x, Double_t *par)
{
        Double_t xx =x[0];
        Double_t norm = par[0];
        Double_t mean = par[1];
        Double_t sigma= par[2];
        Double_t f = norm*TMath::Gaus(xx,mean,sigma);
        Double_t yy = mean-xx;
        Double_t norm2= par[3];
        Double_t mean2= par[4];
        Double_t sigma2= par[5];
        f += norm2*TMath::Landau(yy,mean2,sigma2);
        return f;
}


Double_t breicrys(Double_t *x,Double_t *par)
{
  
  Double_t t = (x[0]-par[2])/par[3];
  if (par[0] < 0) t = -t;
  
  Double_t absAlpha = fabs((Double_t)par[0]);
  
  if (t >= -absAlpha) {
    //return par[4]*exp(-0.5*t*t);
    return par[4]*TMath::BreitWigner(x[0],par[2],par[3]);
  }
  else {
    Double_t a =  TMath::Power(par[1]/absAlpha,par[1])*exp(-0.5*absAlpha*absAlpha);
    Double_t b= par[1]/absAlpha - absAlpha;
    
    return par[4]*(a/TMath::Power(b - t, par[1]));
  }
  
}

Double_t myexp(Double_t *x,Double_t *par)
{
  Double_t cons  = par[0];
  Double_t slope = par[1];
  
  Double_t f;
  f = exp(cons + slope*x[0]);
  return f;

}

Double_t mygaus(Double_t *x,Double_t *par)
{
  Double_t xx    = x[0];
  Double_t norm  = par[0];
  Double_t mean  = par[1];
  Double_t sigma = par[2];
  
  Double_t f;
  Double_t tt = (xx-mean)/sigma ;
  f = norm*exp( 0.5*( pow(tt,2) ) );
  return f;
}

Double_t mylandau(Double_t *x, Double_t *par)
{
        Double_t xx =x[0];
	Double_t norm= par[0];
        Double_t mean= par[1];
        Double_t sigma= par[2];
        double f = norm*TMath::Landau(xx,mean,sigma);
        return f;
}


Double_t powerlaw(Double_t *x, Double_t *par)
{
        Double_t xx   =x[0];
	Double_t cons =par[0];
        Double_t b    =par[1];
        Double_t power=par[2];
	double f;
        f = cons + b/pow(xx,power);
        return f;
}


Double_t fallrisepowerlaw(Double_t *x, Double_t *par)
{
  Double_t xx   =x[0];
  Double_t cons1 =par[0];
  Double_t b1    =par[1];
  Double_t power1=par[2];
  Double_t b2    =par[3];
  Double_t b3    =par[4];
  //Double_t b4    =par[5];
  //Double_t b5    =par[6];

  double f;
  //f = cons1 + b1/pow(xx,power1) + b2*pow(xx,2) ;
  //f = cons1 + b1/pow(xx,power1) +  b2*xx + b3*pow(xx,2) ;
  //f = cons1 + b1/pow(xx,power1) +  b2*exp(b3*xx) ;
  //f = cons1 + b1/pow(xx,power1) +  b2*pow(xx,b3) ;
  f = cons1 + b1/pow(xx,power1) +  b2*xx + b3*pow(xx,2);
  //f = cons1 + b1*TMath::Erfc(xx) +  power1*xx + b2*pow(xx,2);
  
  //f = cons1 + b1/pow(xx,power1) - b2*TMath::ASin(b3*xx);
  
  //f = cons1 + b1/pow(xx,power1) +  1./pow(xx,b4) + b2*xx + b3*pow(xx,2);
  //f = cons1 + b1/pow(xx,power1) + b2*xx + b3*pow(xx,b4);
  //f = cons1 + b1/pow(xx,power1) + b3*pow(xx,b2);
  
  return f;
}


