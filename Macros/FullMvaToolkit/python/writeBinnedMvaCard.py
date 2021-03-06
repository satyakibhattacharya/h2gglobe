import ROOT
import os,numpy,sys,math,array
ROOT.gROOT.SetStyle("Plain")
ROOT.gROOT.SetBatch(True)

ROOT.gROOT.ProcessLine("gSystem->SetIncludePath(\"-I$ROOTSYS/include -I$ROOFITSYS/include\")");

ROOT.gROOT.ProcessLine(".L python/quadInterpolate.C+")
from ROOT import quadInterpolate

from optparse import OptionParser

#from BdtToyMaker import BdtToyMaker
from CombinedToyMaker import CombinedToyMaker

g_r=ROOT.TRandom3(0)

# Some Configury global options
g_toydatalist		= []
g_toysiglist = []
g_tmva			= 0
g_SIDEBANDWIDTH		= 0.02
g_expdijet		= 0.00495
#--------------------------

# Some "Global" Variables
nBins_vbf=2
nBins_vh=3

# PLOT OPS ----------------
sigscale   = 1.
# THEORY SYSTEMATICS ------
lumi          = "1.044"
PDF_ggH       = "0.930/1.076"
PDF_qqH       = "0.972/1.026"
PDF_VH        = "0.958/1.042"
PDF_ttH       = "0.920/1.080" 
QCDscale_ggH  = "0.918/1.076"
QCDscale_qqH  = "0.992/1.003"
QCDscale_VH   = "0.982/1.021"
QCDscale_ttH  = "0.906/1.041"

# SHAPE SYSTEMATICS -------
systematics = [
	       "E_res"
	      ,"E_scale"
	      ,"idEff"
	      #,"r9Eff"
	      ,"phoIdMva"
	      ,"regSig"
	      #,"kFactor"
	      ,"triggerEff"
	      #,"pdfWeight"
	      ,"vtxEff"
	      ]

# ADDITIONAL EXLUSIVE TAG SYSTEMATICS --
UEPS_ggH = 0.260
UEPS_qqH = 0.076
UEPS_VH  = 0.260
UEPS_ttH = 0.260

JEC_ggH = 0.110
JEC_qqH = 0.034
JEC_VH  = 0.110
JEC_ttH = 0.110

UEPS_Migration_ggH = 0.045
UEPS_Migration_qqH = 0.100
UEPS_Migration_VH = 0.045
UEPS_Migration_ttH = 0.045

JEC_Migration_ggH  = 0.025
JEC_Migration_qqH  = 0.005
JEC_Migration_VH  = 0.025
JEC_Migration_ttH  = 0.025

PUJetIDEff = 0.02

elec_tag_eff_ggH = 0.0
elec_tag_eff_qqH = 0.0
elec_tag_eff_VH  = 0.01
elec_tag_eff_ttH = 0.01
muon_tag_eff_ggH = 0.0
muon_tag_eff_qqH = 0.0
muon_tag_eff_VH  = 0.01
muon_tag_eff_ttH = 0.01
met_tag_eff_ggH  = 0.15
met_tag_eff_qqH  = 0.15
met_tag_eff_VH   = 0.04
met_tag_eff_ttH  = 0.04

#JetID_gg = 0.5
#JetID_qq = 0.07
#JEC_gg = 0.07
#JEC_qq = 0.04

# -------------------------
def generateFixedNData(backgroundEntries,nToyData):

	returnbins = [0 for b in backgroundEntries]
	totback = sum(backgroundEntries)
	cdfbkg = [float(sum(backgroundEntries[0:j+1]))/totback for j in range(len(backgroundEntries))]

	for i in range(int(nToyData)):
	  unirandom=g_r.Uniform()
	  for bb in range(len(cdfbkg)): 
		if unirandom<=cdfbkg[bb]: returnbins[bb]+=1; break
	
	return returnbins

def tagPseudoDijets():
	#Tag the Dijets of the global toy
	print "Tagging Pseudo Di-jets in Global Toy"
	for p,gtoy in enumerate(g_toydatalist):
		unirandom=g_r.Uniform()
		if unirandom<g_expdijet: g_toydatalist[p]=(1.+g_SIDEBANDWIDTH+gtoy[1],gtoy[1])

def fillToyBDT(histogram):

	toydata = g_toydatalist[:]
	histNew = histogram.Clone()
	for b in range(1,histNew.GetNbinsX()+1): histNew.SetBinContent(b,0)
	for j in range(len(toydata)):
		val = array.array('f',[0])
		if toydata[j][0]>1. : val[0] = toydata[j][0]
		else: val[0] = g_tmva.tmvaGetVal(toydata[j][0],toydata[j][1])	
		histNew.Fill(val[0])
	listret = []
	for b in range(1,histNew.GetNbinsX()+1):listret.append(histNew.GetBinContent(b))
	return listret

def fillAsimovBDT(data,histogram):
	
	toydata = g_toysiglist[:]
	histNew = data.Clone()
	for b in range(1,histNew.GetNbinsX()+1): histNew.SetBinContent(b,0)
	for j in range(len(toydata)):
		val = array.array('f',[0])
		if toydata[j][0]>1. : val[0] = toydata[j][0]
		else: val[0] = g_tmva.tmvaGetVal(toydata[j][0],toydata[j][1])	
		print "input to tmva -> ",toydata[j][0],toydata[j][1]
		print "But inside writeBinnedDatacard bdt, weight",val[0], toydata[j][2]
		histNew.Fill(val[0],options.expSig*toydata[j][2])
		print "Signal is --> ",histNew.Integral()
	for b in range(1,histNew.GetNbinsX()+1): histNew.SetBinContent(b,histNew.GetBinContent(b)+histogram.GetBinContent(b))
	listret = []
	for b in range(1,histNew.GetNbinsX()+1):listret.append(histNew.GetBinContent(b))
	return listret
	
def plainBin(hist):
	nb = hist.GetNbinsX()
	h2 = ROOT.TH1F(hist.GetName()+"new","",nb,0,nb)
	for i in range (1,nb+1):
		h2.SetBinContent(i,hist.GetBinContent(i))
		h2.SetBinError(i,hist.GetBinError(i))
		if (options.includeVBF):
			if hist.GetBinLowEdge(i+1) <= 1.:
			  h2.GetXaxis().SetBinLabel(i,"BDT Bin %d "%(i))
			elif hist.GetBinLowEdge(i+1) <= 1.04:
			  h2.GetXaxis().SetBinLabel(i," Loose di-jet ")
			elif hist.GetBinLowEdge(i+1) <=1.08:
			  h2.GetXaxis().SetBinLabel(i," Tight di-jet ")
			elif hist.GetBinLowEdge(i+1) <=1.12:
			  h2.GetXaxis().SetBinLabel(i," Muon tag ")
			elif hist.GetBinLowEdge(i+1) <=1.16:
			  h2.GetXaxis().SetBinLabel(i," Electron tag ")
			else:
			  h2.GetXaxis().SetBinLabel(i," MET tag ")
	h2.GetXaxis().SetNdivisions(nb)
	return h2

def plotDistributions(mass,data,signals,bkg,errors):

	lumistring = "%1.1f fb^{-1}"%((options.intLumi)/1000.)
	if options.splitSignal: # last signal is separated off
	  for i in range(1,len(signals)-1):
		signals[0].Add(signals[i])
	else:
	  for i in range(1,len(signals)):
		signals[0].Add(signals[i])

	nbins = data.GetNbinsX()

	flatdata    = plainBin(data)
	flatsignal  = plainBin(signals[0])
	flatsignal1 = plainBin(signals[-1])

	flatbkg  = plainBin(bkg);flatbkg.SetLineColor(4);flatbkg.SetLineWidth(2)
	for b in range(1,nbins+1): flatbkg.GetXaxis().SetBinLabel(b,flatdata.GetXaxis().GetBinLabel(b))

	fNew  = flatbkg.Clone()
	fNew2 = flatbkg.Clone()

	flatdata.SetMarkerStyle(20);flatdata.SetMarkerSize(1.0)
		
	fNew.SetLineColor(1);fNew.SetLineWidth(2);fNew.SetFillStyle(1001);fNew.SetFillColor(3)
	fNew2.SetFillColor(5);fNew2.SetLineColor(1);fNew2.SetLineWidth(2);fNew2.SetFillStyle(1001)

	fNewT = fNew.Clone();fNew2T = fNew2.Clone();fNewT.SetFillStyle(1001);fNew2T.SetFillStyle(1001)

	flatsignal.SetLineWidth(2);flatsignal.SetLineColor(ROOT.kRed);flatsignal.Scale(sigscale)
	flatsignal1.SetLineWidth(2);flatsignal1.SetLineColor(ROOT.kGreen+4);flatsignal1.Scale(sigscale)
		
	leg = ROOT.TLegend(0.6,0.59,0.88,0.88);leg.SetFillColor(0);leg.SetBorderSize(0)

	for b in range(1,nbins+1):
		additional = errors[b-1]
  		fNew.SetBinError(b,((fNew.GetBinError(b)**2)+((fNew.GetBinContent(b)*additional)**2))**0.5)
  		fNew2.SetBinError(b,2*(((fNew2.GetBinError(b)**2)+((fNew2.GetBinContent(b)*additional)**2))**0.5))
	c = ROOT.TCanvas();c.SetLogy()
	if (not options.includeVBF): flatdata.GetXaxis().SetTitle("Category")
	flatdata.GetYaxis().SetRangeUser(0.1,1e4)
	fNew2.GetYaxis().SetRangeUser(0.1,1e4)
	if (not options.blind): 
		flatdata.Draw("9")
		fNew2.Draw("9sameE2")
	else: 
		fNew2.Draw("9E2")
	fNew.Draw("9sameE2");flatbkg.Draw("9samehist")
	if options.splitSignal: 
	  sigst = ROOT.THStack();sigst.Add(flatsignal);sigst.Add(flatsignal1);sigst.Draw("9samehist")
	else:  flatsignal.Draw("9samehist")
	if (not options.blind): 
		flatdata.Draw("9sameP");
	flatbkg.SetMinimum(1.0);flatbkg.SetMaximum(20*flatdata.Integral())

	if (not options.blind): leg.AddEntry(flatdata,"Data","PLE")
	if options.splitSignal:
	  leg.AddEntry(flatsignal,"Higgs (GG,WZ,TT), m_{H}=%3.1f GeV (%dxSM)"%(mass,int(sigscale)) ,"L")
	  leg.AddEntry(flatsignal1,"Higgs, m_{H}=%3.1f GeV (%dxSM)"%(mass,int(sigscale)) ,"L")

	else: leg.AddEntry(flatsignal,"Higgs, m_{H}=%3.1f GeV (%dxSM)"%(mass,int(sigscale)) ,"L")
	leg.AddEntry(flatbkg,"Background","L");leg.AddEntry(fNewT,"\pm 1\sigma","F");leg.AddEntry(fNew2T,"\pm 2\sigma","F")
	leg.Draw()
	mytext = ROOT.TLatex();mytext.SetTextSize(0.03);mytext.SetNDC();#mytext.DrawLatex(0.1,0.92,"CMS preliminary,  #sqrt{s} = 8 TeV ");
	mytext.SetTextSize(0.04)
	mytext.DrawLatex(0.25,0.8,"#splitline{CMS preliminary}{L = %s #sqrt{s} = 8 TeV}"%(lumistring))
	leg.Draw()
	c.SaveAs(plotOutDir+"/pdf/model_m%3.1f.pdf"%mass);c.SaveAs(plotOutDir+"/macro/model_m%3.1f.C"%mass);c.SaveAs(plotOutDir+"/png/model_m%3.1f.png"%mass)
	
	d = ROOT.TCanvas()
	leg2 = ROOT.TLegend(0.56,0.56,0.88,0.88)
	leg2.SetFillColor(0);leg2.SetBorderSize(0)
	if (not options.includeVBF): flatdata.GetXaxis().SetTitle("Category")
	flatdata.GetYaxis().SetTitle("Data - Background");
	datErrs = []
	for b in range(1,nbins+1): datErrs.append((flatdata.GetBinContent(b))**0.5);
	flatdata.Add(flatbkg,-1)
	for b in range(1,nbins+1): 
		flatdata.SetBinError(b,((datErrs[b-1]*datErrs[b-1]) +(fNew.GetBinError(b)*fNew.GetBinError(b)))**0.5 )
	flatbkg.Add(flatbkg,-1)

	if (not options.blind): 
		flatdata.Draw("9")
		flatbkg.Draw("9samehist")
	else: 
		flatbkg.Draw("9hist")
	if options.splitSignal: 
	  sigst = ROOT.THStack();sigst.Add(flatsignal);sigst.Add(flatsignal1)
	  sigst.Draw("9samehist")
	else:
	  flatsignal.Draw("9samehist")
	if (not options.blind): 
		flatdata.Draw("9sameP")
	flatbkg.SetMaximum(250);flatbkg.SetMinimum(-100)

	if (not options.blind): leg2.AddEntry(flatdata,"Data","PLE")
	if options.splitSignal:
	  leg2.AddEntry(flatsignal,"Higgs (GG,WZ,TT), m_{H}=%3.0f GeV (%dxSM)"%(mass,int(sigscale)) ,"L")
	  leg2.AddEntry(flatsignal1,"Higgs, m_{H}=%3.0f GeV (%dxSM)"%(mass,int(sigscale)) ,"L")

	else: leg2.AddEntry(flatsignal,"Higgs, m_{H}=%3.0f GeV (%dxSM)"%(mass,int(sigscale)) ,"L")
	leg2.AddEntry(flatbkg,"Background","L")

	mytext.SetTextSize(0.04)

	leg2.Draw()
	mytext = ROOT.TLatex();mytext.SetTextSize(0.03);mytext.SetNDC();#mytext.DrawLatex(0.1,0.92,"CMS preliminary,  #sqrt{s} = 7 TeV ");
	mytext.SetTextSize(0.04)
	mytext.DrawLatex(0.25,0.8,"#splitline{CMS preliminary}{L = %s #sqrt{s} = 8 TeV}"%(lumistring))
	d.SaveAs(plotOutDir+"/pdf/diff_model_m%3.1f.pdf"%mass);d.SaveAs(plotOutDir+"/macro/diff_model_m%3.1f.C"%mass);d.SaveAs(plotOutDir+"/png/diff_model_m%3.1f.png"%mass)
	


#def getBinningMass(mass):

#	if mass >= 115.0 and mass <= 117.0: return "115"
#	if mass >= 117.5 and mass <= 122.0: return "120"
#	if mass >= 122.5 and mass <= 127.0: return "125"
#	if mass >= 127.5 and mass <= 132.0: return "130"
#	if mass >= 132.5 and mass <= 137.0: return "135"
#	if mass >= 137.5 and mass <= 144.5: return "140"
#	if mass >= 145.0 and mass <= 150.0: return "150"

def py_quadInterpolate(C,X1,X2,X3,Y1,Y2,Y3):
	resL = quadInterpolate(-1*C,X1,X2,X3,Y1,Y2,Y3)
	resH = quadInterpolate(C,X1,X2,X3,Y1,Y2,Y3)
	if math.isnan(resL) or math.isinf(resL) or  math.isnan(resH) or math.isinf(resL): return " - "
	if abs(resL - 1) < 0.00001 or abs(resL - 1) > 1: return " - "
	if abs(resH - 1) < 0.00001 or abs(resH - 1) > 1: return " - "
	return " %.3f/%.3f "%(resL,resH) 

def getBinContent(hist,b):
  
	res = hist.GetBinContent(b)
	if res==0: return 0.0001
	else: return res

def getPoissonBinContent(hist,b,exp):
  
	res = exp*(hist.GetBinContent(b))
#	if res==0: return 0.0001
	return g_r.Poisson(res)

def writeCard(tfile,mass,scaleErr):

  lumistring = "%1.1f fb^{-1}"%(options.intLumi)
  print "Writing Datacard for mass -> ", mass
  outPut = open(cardOutDir+"/mva-datacard_"+runtype+"_%3.1f.txt"%mass,"w")

  # Get All of the histograms we are going to use
  # Data ->
  dataHist = tfile.Get("th1f_data_"+runtype+"_%3.1f"%mass)
  nBins    = dataHist.GetNbinsX()
  print "Number of Channels -> ", nBins
  # bkg model ->
  bkgHist  	= tfile.Get("th1f_bkg_"+runtype+"_%3.1f"%mass)
  
  if options.Bias: bkgHistCorr   = tfile.Get("th1f_bkg_"+runtype+"_%3.1f_fitsb_biascorr"%mass)
  #if options.Bias: bkgHistCorr   = tfile.Get("th1f_bkg_mc_"+runtype+"_%3.1f"%mass)
  # 4 signal channels ->
  gghHist  = tfile.Get("th1f_sig_"+runtype+"_ggh_%3.1f"%mass)
  vbfHist  = tfile.Get("th1f_sig_"+runtype+"_vbf_%3.1f"%mass)
  wzhHist  = tfile.Get("th1f_sig_"+runtype+"_wzh_%3.1f"%mass)
  tthHist  = tfile.Get("th1f_sig_"+runtype+"_tth_%3.1f"%mass)

  if options.signalyieldsweight > 0:
    print "Re-weighting Signal yields x %d"%signalyieldsweight
    gghHist.Scale(signalyieldsweight)
    vbfHist.Scale(signalyieldsweight)
    wzhHist.Scale(signalyieldsweight)
    tthHist.Scale(signalyieldsweight)
 
  ###############################################################################
  # Write the basics
  outPut.write("Mva Binned Analysis DataCard (mH=%3.1f) \n"%mass)
  outPut.write("DataCard extracted from %s \n"%tfile.GetName())
  outPut.write("--------------------------------------------------------------\n")
  outPut.write("imax *\n")
  outPut.write("jmax *\n")
  outPut.write("kmax *\n")
  outPut.write("--------------------------------------------------------------\n")
  ## Now its the observation
  outPut.write("bin 	     ")
  binL=1
  binH=nBins+1
  if options.binfromright>-1:
    binL=nBins+1-options.binfromright
    binH=binL+1
    if binL<1:
      sys.exit("Not enough bins to write %d" %options.binfromright)
  for b in range(binL,binH): outPut.write(" cat%d "%b)
  outPut.write("\nobservation")

#  backgroundContents = [bkgHist.GetBinContent(b) for b in range(1,nBins+1)]
  backgroundContents = []
  if options.Bias:
	print "Using Bkg Model Corrected for mass bias"
	backgroundContents = [bkgHistCorr.GetBinContent(b) for b in range(1,nBins+1)]
  else: sys.exit("Simple Background model no longer available !!!! ")

  if options.throwToy or options.throwGlobalToy or options.throwAsimov:
        print "Throwing toy dataset"

#	if options.throwGlobalToy: pseudoBackgroundOnlyDataset=generateFixedNData(backgroundContents,g_normalisation_toy)
	if options.throwGlobalToy and not options.throwAsimov :pseudoBackgroundOnlyDataset=fillToyBDT(dataHist)
	else: pseudoBackgroundOnlyDataset=[g_r.Poisson(backgroundContents[b-1]) for b in range(1,nBins+1)]

	if options.throwAsimov: pseudoBackgroundOnlyDataset=fillAsimovBDT(dataHist,bkgHistCorr)

	for b in range(1,nBins+1): 
		nd = pseudoBackgroundOnlyDataset[b-1]
		ns = 0
		if options.expSig>0 and not options.throwGlobalToy and not options.throwAsimov:
			print "Injecting %.f x SM"%options.expSig
			ns+=getPoissonBinContent(gghHist,b,options.expSig)
			ns+=getPoissonBinContent(vbfHist,b,options.expSig)
			ns+=getPoissonBinContent(wzhHist,b,options.expSig)
			ns+=getPoissonBinContent(tthHist,b,options.expSig)
		
		print 'here'
		if options.throwAsimov: outPut.write(" %.2f "%(nd+ns))
		else: outPut.write(" %d "%(nd+ns))
		dataHist.SetBinContent(b,nd+ns)
		dataHist.SetBinError(b,(nd+ns)**0.5)

  else:
	for b in range(binL,binH): outPut.write(" %d "%dataHist.GetBinContent(b))
  outPut.write("\n--------------------------------------------------------------\n")
  ## Now we do the signal and background parts
  outPut.write("bin 	     ")
  for b in range(binL,binH): outPut.write(" cat%d  cat%d  cat%d  cat%d  cat%d "%(b,b,b,b,b))
  outPut.write("\nprocess    ")
  for b in range(binL,binH): outPut.write("  ggh    vbf    wzh    tth    bkg  ")
  outPut.write("\nprocess    ")
  for b in range(binL,binH): outPut.write("   0      0      0      0    1    ")
  outPut.write("\nrate       ")

  # if global toy need to randomise background within its error as well

  if options.randomizeBackground:
    # get signed error matrix from fit
    th2f_errmat = tfile.Get("fUncorrErr_%s_%3.1f"%(options.bdtType,mass))
    for b in range(binL,binH):
      # first randomise by scale error
      randBkg = backgroundContents[b-1]*(scaleErr**(1+g_r.Gaus()))

    # then randomise by bin to bin correlation error
      for q in range(1,nBins):
        berr = th2f_errmat.GetBinContent(q,b)
        bkgCont = backgroundContents[b-1]/sum(backgroundContents)
        bias = quadInterpolate(1.,-1.,0.,1.,bkgCont-berr,bkgCont,bkgCont+berr)
        randBkg = randBkg*(bias**(1+g_r.Gaus()))
      
      outPut.write(" %.3f   %.3f   %.3f   %.3f   %.3f "\
      %(getBinContent(gghHist,b),getBinContent(vbfHist,b),getBinContent(wzhHist,b),getBinContent(tthHist,b)\
       ,randBkg))
    outPut.write("\n--------------------------------------------------------------\n")

  else:
    for b in range(binL,binH): outPut.write(" %.3f   %.3f   %.3f   %.3f   %.3f "\
      %(getBinContent(gghHist,b),getBinContent(vbfHist,b),getBinContent(wzhHist,b),getBinContent(tthHist,b)\
       ,backgroundContents[b-1]))
    outPut.write("\n--------------------------------------------------------------\n")


  # This next bit is for the signal systematics, first lets do the easy ones, lumi and theory
  outPut.write("\nlumi       lnN ")
  for b in range(binL,binH): outPut.write(" %s  %s  %s  %s  -  "%(lumi,lumi,lumi,lumi))

  if options.theorySys:
    outPut.write("\nQCDscale_ggH  lnN ")
    for b in range(binL,binH): outPut.write(" %s  -   -   -   -  "%(QCDscale_ggH))
    outPut.write("\nQCDscale_qqH  lnN ")
    for b in range(binL,binH): outPut.write(" -   %s  -   -   -  "%(QCDscale_qqH))
    outPut.write("\nQCDscale_VH   lnN ")
    for b in range(binL,binH): outPut.write(" -   -   %s  -   -  "%(QCDscale_VH))
    outPut.write("\nQCDscale_ttH  lnN ")
    for b in range(binL,binH): outPut.write(" -   -   -   %s  -  "%(QCDscale_ttH))
    outPut.write("\nPDF_ggH  lnN ")
    for b in range(binL,binH): outPut.write(" %s  -   -   -   -  "%(PDF_ggH))
    outPut.write("\nPDF_qqH  lnN ")
    for b in range(binL,binH): outPut.write(" -   %s  -   -   -  "%(PDF_qqH))
    outPut.write("\nPDF_VH   lnN ")
    for b in range(binL,binH): outPut.write(" -   -   %s  -   -  "%(PDF_VH))
    outPut.write("\nPDF_ttH  lnN ")
    for b in range(binL,binH): outPut.write(" -   -   -   %s  -  "%(PDF_ttH))

  outPut.write("\n")

  # includeVBF means the last bin is the VBF tagged bin and we apply and additional 
  # 70% GGH(TTH) and 10% on the VBF(WZH) part of that category (configurable above)
  nBins_inclusive=0
  if options.includeVBF:
    print "Including VBF Systematics"
    for b in range(binL,nBins+1):  
	if dataHist.GetBinLowEdge(b)<1: nBins_inclusive+=1

    nBins_exclusive=nBins_vbf+nBins_vh
    print "Number of Non VBF channels -> ", nBins_inclusive
    print "Number of VBF channels -> ", nBins_vbf
    print "Number of VH channels -> ", nBins_vh
    print "Number of Exclu channels -> ", nBins_exclusive

    # First is UEPS
    # calculate the effect on each bin
    numberOfGGH_dijet = sum([gghHist.GetBinContent(b)*UEPS_ggH for b in range(binH-nBins_exclusive,binH-nBins_vh)])
    numberOfTTH_dijet = sum([tthHist.GetBinContent(b)*UEPS_ttH for b in range(binH-nBins_exclusive,binH-nBins_vh)])
    numberOfVBF_dijet = sum([vbfHist.GetBinContent(b)*UEPS_qqH for b in range(binH-nBins_exclusive,binH-nBins_vh)])
    numberOfWZH_dijet = sum([wzhHist.GetBinContent(b)*UEPS_VH  for b in range(binH-nBins_exclusive,binH-nBins_vh)])
    
    numberOfGGH_incl  = sum([gghHist.GetBinContent(b) for b in range(binL,nBins_inclusive+binL)])
    numberOfTTH_incl  = sum([tthHist.GetBinContent(b) for b in range(binL,nBins_inclusive+binL)])
    numberOfVBF_incl  = sum([vbfHist.GetBinContent(b) for b in range(binL,nBins_inclusive+binL)])
    numberOfWZH_incl  = sum([wzhHist.GetBinContent(b) for b in range(binL,nBins_inclusive+binL)])

    outPut.write("\nUEPS  lnN ")
    
    # inclusive bins
    for b in range(binL,nBins_inclusive+binL): outPut.write(" %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -  "%\
		    (1.-(numberOfGGH_dijet/numberOfGGH_incl),1.+(numberOfGGH_dijet/numberOfGGH_incl),\
		     1.-(numberOfVBF_dijet/numberOfVBF_incl),1.+(numberOfVBF_dijet/numberOfVBF_incl),\
		     1.-(numberOfWZH_dijet/numberOfWZH_incl),1.+(numberOfWZH_dijet/numberOfWZH_incl),\
		     1.-(numberOfTTH_dijet/numberOfTTH_incl),1.+(numberOfTTH_dijet/numberOfTTH_incl)))
    # exclusive bins - vbf
    for b in range(binH-nBins_exclusive,binH-nBins_vh): outPut.write(" %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -  "%\
      (1+UEPS_ggH,1-UEPS_ggH,1+UEPS_qqH,1-UEPS_qqH,1+UEPS_VH,1-UEPS_VH,1+UEPS_ttH,1-UEPS_ttH))
    # exclusive bins - vh
    for b in range(binH-nBins_vh,binH): outPut.write(" -   -   -   -   -  ")
    outPut.write("\n")

    # Next is JEC
    numberOfGGH_dijet = sum([gghHist.GetBinContent(b)*JEC_ggH for b in range(binH-nBins_exclusive,binH-nBins_vh)])
    numberOfTTH_dijet = sum([tthHist.GetBinContent(b)*JEC_ttH for b in range(binH-nBins_exclusive,binH-nBins_vh)])
    numberOfVBF_dijet = sum([vbfHist.GetBinContent(b)*JEC_qqH for b in range(binH-nBins_exclusive,binH-nBins_vh)])
    numberOfWZH_dijet = sum([wzhHist.GetBinContent(b)*JEC_VH  for b in range(binH-nBins_exclusive,binH-nBins_vh)])
    
    numberOfGGH_incl  = sum([gghHist.GetBinContent(b) for b in range(binL,nBins_inclusive+binL)])
    numberOfTTH_incl  = sum([tthHist.GetBinContent(b) for b in range(binL,nBins_inclusive+binL)])
    numberOfVBF_incl  = sum([vbfHist.GetBinContent(b) for b in range(binL,nBins_inclusive+binL)])
    numberOfWZH_incl  = sum([wzhHist.GetBinContent(b) for b in range(binL,nBins_inclusive+binL)])

    outPut.write("\nJEC   lnN")
    # inclusive bins
    for b in range(binL,nBins_inclusive+binL): outPut.write(" %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -  "%\
		    (1.-(numberOfGGH_dijet/numberOfGGH_incl),1.+(numberOfGGH_dijet/numberOfGGH_incl),\
		     1.-(numberOfVBF_dijet/numberOfVBF_incl),1.+(numberOfVBF_dijet/numberOfVBF_incl),\
		     1.-(numberOfWZH_dijet/numberOfWZH_incl),1.+(numberOfWZH_dijet/numberOfWZH_incl),\
		     1.-(numberOfTTH_dijet/numberOfTTH_incl),1.+(numberOfTTH_dijet/numberOfTTH_incl)))
    # exclusive bins - vbf
    for b in range(binH-nBins_exclusive,binH-nBins_vh): outPut.write(" %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -  "%\
      (1+JEC_ggH,1-JEC_ggH,1+JEC_qqH,1-JEC_qqH,1+JEC_VH,1-JEC_VH,1+JEC_ttH,1-JEC_ttH))
    # exclusive bins - vh
    for b in range(binH-nBins_vh,binH): outPut.write(" -   -   -   -   -  ")

    # Now do PUJetID
    numberOfGGH_dijet = sum([gghHist.GetBinContent(b)*PUJetIDEff for b in range(binH-nBins_exclusive,binH-nBins_vh)])
    numberOfTTH_dijet = sum([tthHist.GetBinContent(b)*PUJetIDEff for b in range(binH-nBins_exclusive,binH-nBins_vh)])
    numberOfVBF_dijet = sum([vbfHist.GetBinContent(b)*PUJetIDEff for b in range(binH-nBins_exclusive,binH-nBins_vh)])
    numberOfWZH_dijet = sum([wzhHist.GetBinContent(b)*PUJetIDEff for b in range(binH-nBins_exclusive,binH-nBins_vh)])
    
    numberOfGGH_incl  = sum([gghHist.GetBinContent(b) for b in range(binL,nBins_inclusive+binL)])
    numberOfTTH_incl  = sum([tthHist.GetBinContent(b) for b in range(binL,nBins_inclusive+binL)])
    numberOfVBF_incl  = sum([vbfHist.GetBinContent(b) for b in range(binL,nBins_inclusive+binL)])
    numberOfWZH_incl  = sum([wzhHist.GetBinContent(b) for b in range(binL,nBins_inclusive+binL)])

    outPut.write("\nCMS_eff_j   lnN")
    # inclusive bins
    for b in range(binL,nBins_inclusive+binL): outPut.write(" %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -  "%\
		    (1.-(numberOfGGH_dijet/numberOfGGH_incl),1.+(numberOfGGH_dijet/numberOfGGH_incl),\
		     1.-(numberOfVBF_dijet/numberOfVBF_incl),1.+(numberOfVBF_dijet/numberOfVBF_incl),\
		     1.-(numberOfWZH_dijet/numberOfWZH_incl),1.+(numberOfWZH_dijet/numberOfWZH_incl),\
		     1.-(numberOfTTH_dijet/numberOfTTH_incl),1.+(numberOfTTH_dijet/numberOfTTH_incl)))
    # exclusive bins - vbf
    for b in range(binH-nBins_exclusive,binH-nBins_vh): outPut.write(" %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -  "%\
      (1+PUJetIDEff,1-PUJetIDEff,1+PUJetIDEff,1-PUJetIDEff,1+PUJetIDEff,1-PUJetIDEff,1+PUJetIDEff,1-PUJetIDEff))
    # exclusive bins - vh
    for b in range(binH-nBins_vh,binH): outPut.write(" -   -   -   -   -  ")

    # Now do UEPSMigration    
    outPut.write("\nUEPSMigration  lnN")
    numberOfGGH_loose = gghHist.GetBinContent(binL+nBins_inclusive)*UEPS_Migration_ggH
    numberOfVBF_loose = vbfHist.GetBinContent(binL+nBins_inclusive)*UEPS_Migration_qqH
    numberOfWZH_loose = wzhHist.GetBinContent(binL+nBins_inclusive)*UEPS_Migration_VH
    numberOfTTH_loose = tthHist.GetBinContent(binL+nBins_inclusive)*UEPS_Migration_ttH
    numberOfGGH_tight = gghHist.GetBinContent(binH-nBins_vh) if gghHist.GetBinContent(binH-nBins_vh)>0 else 1.e10
    numberOfVBF_tight = vbfHist.GetBinContent(binH-nBins_vh) if vbfHist.GetBinContent(binH-nBins_vh)>0 else 1.e10
    numberOfWZH_tight = wzhHist.GetBinContent(binH-nBins_vh) if wzhHist.GetBinContent(binH-nBins_vh)>0 else 1.e10
    numberOfTTH_tight = tthHist.GetBinContent(binH-nBins_vh) if tthHist.GetBinContent(binH-nBins_vh)>0 else 1.e10

    if abs(numberOfGGH_loose/numberOfGGH_tight)>1.: numberOfGGH_loose=0.
    if abs(numberOfVBF_loose/numberOfVBF_tight)>1.: numberOfVBF_loose=0.
    if abs(numberOfWZH_loose/numberOfWZH_tight)>1.: numberOfWZH_loose=0.
    if abs(numberOfTTH_loose/numberOfTTH_tight)>1.: numberOfTTH_loose=0.

    for b in range(binL,nBins_inclusive+binL): outPut.write(" -   -   -   -   -")
    if nBins_vbf>0 : outPut.write(" %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -  "%\
        (1+UEPS_Migration_ggH,1-UEPS_Migration_ggH,1+UEPS_Migration_qqH,1-UEPS_Migration_qqH,1+UEPS_Migration_VH,1-UEPS_Migration_VH,1+UEPS_Migration_ttH,1-UEPS_Migration_ttH,\
		     1.-(numberOfGGH_loose/numberOfGGH_tight),1.+(numberOfGGH_loose/numberOfGGH_tight),\
		     1.-(numberOfVBF_loose/numberOfVBF_tight),1.+(numberOfVBF_loose/numberOfVBF_tight),\
		     1.-(numberOfWZH_loose/numberOfWZH_tight),1.+(numberOfWZH_loose/numberOfWZH_tight),\
		     1.-(numberOfTTH_loose/numberOfTTH_tight),1.+(numberOfTTH_loose/numberOfTTH_tight)))
    if nBins_vh: outPut.write(" -   -   -   -   - -   -   -   -   - -   -   -   -   - \n")
  
    # Now do JECMigration    
    outPut.write("\nJECMigration  lnN")
    numberOfGGH_loose = gghHist.GetBinContent(binL+nBins_inclusive)*JEC_Migration_ggH
    numberOfVBF_loose = vbfHist.GetBinContent(binL+nBins_inclusive)*JEC_Migration_qqH
    numberOfWZH_loose = wzhHist.GetBinContent(binL+nBins_inclusive)*JEC_Migration_VH
    numberOfTTH_loose = tthHist.GetBinContent(binL+nBins_inclusive)*JEC_Migration_ttH
    numberOfGGH_tight = gghHist.GetBinContent(binH-nBins_vh) if gghHist.GetBinContent(binH-nBins_vh)>0 else 1.e10
    numberOfVBF_tight = vbfHist.GetBinContent(binH-nBins_vh) if vbfHist.GetBinContent(binH-nBins_vh)>0 else 1.e10
    numberOfWZH_tight = wzhHist.GetBinContent(binH-nBins_vh) if wzhHist.GetBinContent(binH-nBins_vh)>0 else 1.e10
    numberOfTTH_tight = tthHist.GetBinContent(binH-nBins_vh) if tthHist.GetBinContent(binH-nBins_vh)>0 else 1.e10

    if abs(numberOfGGH_loose/numberOfGGH_tight)>1.: numberOfGGH_loose=0.
    if abs(numberOfVBF_loose/numberOfVBF_tight)>1.: numberOfVBF_loose=0.
    if abs(numberOfWZH_loose/numberOfWZH_tight)>1.: numberOfWZH_loose=0.
    if abs(numberOfTTH_loose/numberOfTTH_tight)>1.: numberOfTTH_loose=0.

    for b in range(binL,nBins_inclusive+binL): outPut.write(" -   -   -   -   -")
    if nBins_vbf>0 :outPut.write(" %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -  "%\
        (1+JEC_Migration_ggH,1-JEC_Migration_ggH,1+JEC_Migration_qqH,1-JEC_Migration_qqH,1+JEC_Migration_VH,1-JEC_Migration_VH,1+JEC_Migration_ttH,1-JEC_Migration_ttH,\
		     1.-(numberOfGGH_loose/numberOfGGH_tight),1.+(numberOfGGH_loose/numberOfGGH_tight),\
		     1.-(numberOfVBF_loose/numberOfVBF_tight),1.+(numberOfVBF_loose/numberOfVBF_tight),\
		     1.-(numberOfWZH_loose/numberOfWZH_tight),1.+(numberOfWZH_loose/numberOfWZH_tight),\
		     1.-(numberOfTTH_loose/numberOfTTH_tight),1.+(numberOfTTH_loose/numberOfTTH_tight)))
    if nBins_vh>0 :outPut.write(" -   -   -   -   - -   -   -   -   - -   -   -   -   - \n")
  
  # Now do other exclusive tag systematics
  # muon tag
  outPut.write("\nCMS_eff_m   lnN    ")
  for b in range(binL,nBins_inclusive+nBins_vbf+binL): outPut.write(" -   -   -   -   -")
  if nBins_vh>0: outPut.write(" %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -  "%(1.-muon_tag_eff_ggH,1.+muon_tag_eff_ggH,1.-muon_tag_eff_qqH,1.+muon_tag_eff_qqH,1.-muon_tag_eff_VH,1.+muon_tag_eff_VH,1.-muon_tag_eff_ttH,1.+muon_tag_eff_ttH))
  for b in range(nBins_vbf+binL+2,binH): outPut.write(" -   -   -   -   -")
  # electron tag
  outPut.write("\nCMS_eff_e   lnN    ")
  for b in range(binL,nBins_inclusive+nBins_vbf+binL+1): outPut.write(" -   -   -   -   -")
  if nBins_vh>0: outPut.write(" %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -  "%(1.-elec_tag_eff_ggH,1.+elec_tag_eff_ggH,1.-elec_tag_eff_qqH,1.+elec_tag_eff_qqH,1.-elec_tag_eff_VH,1.+elec_tag_eff_VH,1.-elec_tag_eff_ttH,1.+elec_tag_eff_ttH))
  for b in range(nBins_vbf+binL+3,binH): outPut.write(" -   -   -   -   -")
  # MET tag
  outPut.write("\nCMS_eff_met   lnN    ")
  for b in range(binL,nBins_inclusive+nBins_vbf+binL+2): outPut.write(" -   -   -   -   -")
  if nBins_vh>0: outPut.write(" %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   %.3f/%.3f   -  "%(1.-met_tag_eff_ggH,1.+met_tag_eff_ggH,1.-met_tag_eff_qqH,1.+met_tag_eff_qqH,1.-met_tag_eff_VH,1.+met_tag_eff_VH,1.-met_tag_eff_ttH,1.+met_tag_eff_ttH))
  
  outPut.write("\n")

  # Now is the very tedious part of the signal shape systematics, for each shape, simply do -/+ sigma
  
  if options.signalSys:
   print "Writing Systematics Part (could be slow)"
   for sys in systematics:

    gghHistU  = tfile.Get("th1f_sig_"+runtype+"_ggh_%3.1f_%sUp01_sigma"%(mass,sys))
    vbfHistU  = tfile.Get("th1f_sig_"+runtype+"_vbf_%3.1f_%sUp01_sigma"%(mass,sys))
    wzhHistU  = tfile.Get("th1f_sig_"+runtype+"_wzh_%3.1f_%sUp01_sigma"%(mass,sys))
    tthHistU  = tfile.Get("th1f_sig_"+runtype+"_tth_%3.1f_%sUp01_sigma"%(mass,sys))
    gghHistD  = tfile.Get("th1f_sig_"+runtype+"_ggh_%3.1f_%sDown01_sigma"%(mass,sys))
    vbfHistD  = tfile.Get("th1f_sig_"+runtype+"_vbf_%3.1f_%sDown01_sigma"%(mass,sys))
    wzhHistD  = tfile.Get("th1f_sig_"+runtype+"_wzh_%3.1f_%sDown01_sigma"%(mass,sys))
    tthHistD  = tfile.Get("th1f_sig_"+runtype+"_tth_%3.1f_%sDown01_sigma"%(mass,sys))
    
    #print gghHistU.GetName(), vbfHistU.GetName(), wzhHistU.GetName(), tthHistU.GetName() 
    #print gghHistD.GetName(), vbfHistD.GetName(), wzhHistD.GetName(), tthHistD.GetName() 

    if options.signalyieldsweight > 0:
      gghHistU.Scale(signalyieldsweight)
      vbfHistU.Scale(signalyieldsweight)
      wzhHistU.Scale(signalyieldsweight)
      tthHistU.Scale(signalyieldsweight)
      gghHistD.Scale(signalyieldsweight)
      vbfHistD.Scale(signalyieldsweight)
      wzhHistD.Scale(signalyieldsweight)
      tthHistD.Scale(signalyieldsweight)

    if options.is2011: outPut.write("\n%s lnN "%sys)
    else: outPut.write("\n%s lnN "%sys)

    for b in range(binL,binH):
	 outPut.write(" %s %s %s %s - "%(\
				     py_quadInterpolate(1.,-3.,0.,3.,gghHistD.GetBinContent(b)  \
				        			  ,gghHist.GetBinContent(b)  \
                                        			  ,gghHistU.GetBinContent(b)) \
				    ,py_quadInterpolate(1.,-3.,0.,3.,vbfHistD.GetBinContent(b)  \
				        			  ,vbfHist.GetBinContent(b)  \
                                        			  ,vbfHistU.GetBinContent(b)) \
				    ,py_quadInterpolate(1.,-3.,0.,3.,wzhHistD.GetBinContent(b)  \
				        			  ,wzhHist.GetBinContent(b)  \
                                        			  ,wzhHistU.GetBinContent(b)) \
				    ,py_quadInterpolate(1.,-3.,0.,3.,tthHistD.GetBinContent(b)  \
				        			  ,tthHist.GetBinContent(b)  \
                                        			  ,tthHistU.GetBinContent(b)) \
 				    ))
  outPut.write("\n")
  # Finally the background errors, these are realtively simple
  if options.is2011: outPut.write("\nbkg_norm lnN ")
  else: outPut.write("\nbkg_norm_8TeV lnN ")
  for b in range(binL,binH): outPut.write(" -   -   -   -  %.3f "%(scaleErr))

  ## now for the David errors
  if options.Bias:
	print "Including Mass Bias nuisances (bin-to-bin stat error included)"

	# Input Signed Error Matrix from Fit 
	th2f_errmatrix = tfile.Get("fUncorrErr_%s_%3.1f"%(options.bdtType,mass))
	for b in range(1,nBins):  # This error matrix is nBins-1 X nBins-1 due to constraint on sum on fractions
           if options.is2011: outPut.write("\nmassBias%d lnN"%b)
           else: outPut.write("\nmassBias%d_8TeV lnN"%b)
	   for q in range(binL,binH):
	   	f_errentry = th2f_errmatrix.GetBinContent(b,q)
		bkgC = backgroundContents[q-1]/sum(backgroundContents)
		bias_nuis  = py_quadInterpolate(1.,-1.,0.,1.,bkgC-f_errentry,bkgC,bkgC+f_errentry)
		outPut.write(" - - - - %s "%(bias_nuis))
        	
        outPut.write("\n")
	

  if options.B2B and (not options.Bias):
   # bkg bins will be gmN errors instead 
   for b in range(binL,binH):
        bkgScale = bkgHist.Integral()/bkgHist.GetEntries()
        if options.is2011: outPut.write("\nbkg_stat%d gmN %d "%(b,int(backgroundContents[b-1]/bkgScale)))
        else: outPut.write("\nbkg_stat%d_8TeV gmN %d "%(b,int(backgroundContents[b-1]/bkgScale)))
	for q in range(binL,binH):
		if q==b: outPut.write(" - - - - %.3f "%bkgScale)
		else:    outPut.write(" - - - - - ")

  # Finally make a plot of what will go into the limit
  if options.makePlot: 
	print "Plotting Limit Setting inputs to m%3.1f.pdf"%mass
	if options.Bias : plotBKG = bkgHistCorr.Clone()
	else: plotBKG = bkgHist.Clone()
	plotDistributions(mass,dataHist.Clone() \
			,[gghHist.Clone(),wzhHist.Clone(),tthHist.Clone(),vbfHist.Clone()]\
			,plotBKG \
			,[scaleErr-1. for b in range(nBins)])# put VBF at the end for plot option

  outPut.write("\n")  # done
  outPut.close()
    
#################################################################################  

parser = OptionParser()
parser.add_option("-i","--input",dest="tfileName",help="Input file")
parser.add_option("","--intLumi",dest="intLumi",type="float")
parser.add_option("","--is2011",dest="is2011",action="store_true",default=False)
parser.add_option("","--noB2B",action="store_false",dest="B2B",default=True)
#parser.add_option("","--addBias",dest="biasFile",default=None)
parser.add_option("","--noBias",dest="Bias",default=True,action="store_false")
parser.add_option("","--noSignalSys",action="store_false",dest="signalSys",default=True)
parser.add_option("","--noTheorySys",action="store_false",dest="theorySys",default=True)
parser.add_option("","--throwToy",action="store_true",dest="throwToy",default=False)
parser.add_option("","--throwGlobalToy",action="store_true",dest="throwGlobalToy",default=False)
parser.add_option("","--throwAsimov",action="store_true",dest="throwAsimov",default=False)
parser.add_option("","--expSig",dest="expSig",default=-1.,type="float")
parser.add_option("","--makePlot",dest="makePlot",default=False,action="store_true")
parser.add_option("","--blind",dest="blind",default=False,action="store_true")
parser.add_option("","--noVbfTag",dest="includeVBF",default=True,action="store_false")
parser.add_option("","--noVHTag",dest="includeVH",default=True,action="store_false")
parser.add_option("","--plotStackedVbf",dest="splitSignal",default=False,action="store_true")
parser.add_option("","--inputMassFacWS",dest="inputmassfacws",default="/vols/cms02/h2g/latest_workspace/CMS-HGG_massfac_full_110_150_1.root")
parser.add_option("","--outputMassFacToy",dest="outputmassfactoy",default="massfac_toy_ws.root")
parser.add_option("","--inputBdtPdf",dest="inputpdfworkspace")
parser.add_option("","--outputBdtPdf",dest="outputpdfworkspace",default="combToyWS.root")
parser.add_option("","--inputTrees",dest="treefilename")
parser.add_option("","--dataBdtTree",dest="datatreename",default="dataTree")
parser.add_option("","--signalModelTree",dest="signaltreename",default="sigtree")
parser.add_option("","--randomizeBackground",dest="randomizeBackground",default=False,action="store_true")
parser.add_option("","--tmvaWeightsFolder",dest="tmvaweightsfolder",default="/vols/cms02/h2g/weights/wt_19Feb/")
parser.add_option("","--reweightSignalYields",dest="signalyieldsweight",default=-999.,type="float")
parser.add_option("-b","--specificBin",dest="binfromright",default=-1,type="int")
parser.add_option("-m","--mass",dest="singleMass",default=-1.,type="float")
parser.add_option("-t","--type",dest="bdtType",default="grad");
parser.add_option("-o","--outputDir",dest="outputDir",default="mva-datacards-")
parser.add_option("-p","--outputPlot",dest="outputPlot")
parser.add_option("-l","--mhLow",dest="mhLow",type="float",default=110.)
parser.add_option("-u","--mhHigh",dest="mhHigh",type="float",default=150.)
parser.add_option("-s","--mhStep",dest="mhStep",type="float",default=0.5)
(options,args)=parser.parse_args()

if options.throwAsimov : options.throwGlobalToy = True

print "Creating Binned Datacards from workspace -> ", options.tfileName
if options.throwToy: print ("Throwing Toy dataset from BKG")
if options.throwGlobalToy: print ("Throwing Global Toy dataset from BKG"); options.throwToy=True
if options.expSig > 0: print ("(Also throwing signal SMx%f)"%options.expSig)

if not options.includeVBF: options.splitSignal=False
if (not options.Bias) and options.includeVBF: sys.exit("Cannot use summed sideband (ie assume no mH dependance) for VBF (currently unsupported)")

runtype=options.bdtType

# create output folders
if options.outputDir=="mva-datacards-":
  cardOutDir=options.outputDir+runtype
  plotOutDir="mva-plots-"+runtype
else:
  cardOutDir=options.outputDir
  plotOutDir=cardOutDir+"-plots"

if options.outputPlot:
  plotOutDir=options.outputPlot

if options.binfromright>-1: cardOutDir+="-bin%i"%options.binfromright
if not options.signalSys:
  cardOutDir+="-nosigsys"
if not os.path.isdir(cardOutDir):
  os.makedirs(cardOutDir)
if options.makePlot:
  if not os.path.isdir(plotOutDir):
    os.makedirs(plotOutDir)

#if options.biasFile:
#	biasROOTFile = ROOT.TFile(options.biasFile)

genMasses     = [110,115,120,125,130,135,140,145,150]
#scalingErrors = [1.008,1.008,1.008,1.008,1.008,1.009,1.01,1.011] # Takes from P.Dauncey studies -> 7% window
#scalingErrors =  [1.007,1.007,1.006,1.008,1.007,1.008,1.009,1.01] # Takes from P.Dauncey studies -> 2% window
#scalingErrors = [1.013,1.013,1.012,1.012,1.014,1.015,1.016,1.016] # Takes from P.Dauncey studies -> 7% window (100-180)
#scalingErrors = [1.011,1.01,1.009,1.011,1.011,1.013,1.014,1.014] 	  # Takes from P.Dauncey studies -> 2% window (100-180)
#scalingErrors = [1.00815,1.01024,1.01076,1.01197,1.0099,1.009,1.00928,1.01054 ] 	  # Takes from P.Dauncey studies -> 2% window (100-180) / MIT Preselection
#scalingErrors = [ 1.008,1.008,1.008,1.008,1.01,1.010,1.011,1.012,1.012] # P.Dauncey 100-180 2% window /MIT preselction +BDT>-0.5
#scalingErrors = [1.0136,1.0152,1.01425,1.01102,1.01283,1.01568,1.02157,1.02467,1.02466] # P.Dauncey 100-180, 2% window, MIT presel + BDT > 0.05 (Pow2 Fit)
#scalingErrors = [1.0119,1.01277,1.01203,1.00998,1.01213,1.0141,1.01822,1.02004,1.01954] # P.Dauncey 100-180, 2% window, MIT presel + BDT > 0.05 , after synch(Pow2 Fit)
#scalingErrors = [1.025,1.025,1.025,1.025,1.025,1.025,1.025,1.025,1.025] # FLAT 25%
#scalingErrors = [ 1.01185,1.01292,1.01378,1.01378,1.01594,1.01539,1.01814,1.02052,1.02257] # P.Dauncey 100-180, 2% window, MIT presel + BDT > 0.05 (Pol5 Fit)
#scalingErrors=[1+((s-1)*0.95) for s in scalingErrors]
#scalingErrors = [1.01153,1.01197,1.01102,1.00966,1.01205,1.01457,1.01814,1.01903,1.01768] # P.Dauncey 100-180, 2% window, MIT presel + BDT > 0.05 , after synch, 19Feb (Pow2 Fit)
#scalingErrors = [1.01072,1.01097,1.01061,1.01019,1.01234,1.01306,1.01519,1.01554,1.01412] # P.Dauncey 100-180, 2% window, MIT presel + BDT > 0.05 , Jan16 ReReco 15Apr (Pow2 Fit)
# PAUL NUMBERS - MASS FAC - HCP2012 - 73575 events with 12.2fb-1 - [1.00578,1.00586,1.0056,1.00544,1.00554,1.00542,1.00589,1.00728,1.00884]
# PAUL NUMBERS - MASS FAC - MOR2013 - [1.00444,1.00405,1.00341,1.00342,1.0041,1.00444,1.00447,1.00455,1.00501]

# CUT-BASED at 19.6fb has 141981 events - [1.00957,1.00916,1.00903,1.01011,1.01236,1.01224,1.01257,1.01251,1.01334]

scalingErrors = [1.00444,1.00405,1.00341,1.00342,1.0041,1.00444,1.00447,1.00455,1.00501]
#scalingErrors = [1.005,1.005,1.005,1.005,1.005,1.005,1.005,1.005,1.005]


#evalMasses    = numpy.arange(110,150.5,0.5)
evalMasses    = numpy.arange(options.mhLow,options.mhHigh+options.mhStep,options.mhStep)
normG = ROOT.TGraph(len(genMasses))

# Fill the errors graph
can = ROOT.TCanvas()
for i,ne in enumerate(scalingErrors):
  #err=((scalingErrors[i]-1)*((73575/141981)**0.5))+1 # scale down norm Errors HACK for may31freeze
  err=scalingErrors[i] 
  normG.SetPoint(i,genMasses[i],err)
normG.SetMarkerStyle(20)
normG.GetXaxis().SetTitle("mH")
normG.GetYaxis().SetTitle("(N+dN)/N")
normG.Draw("ALP")
print "Check the Errors Look Sensible -> plot saved to %s/normErrors_%s"%(os.path.dirname(options.tfileName),os.path.basename(options.tfileName))
can.SaveAs(("%s/normErrors_%s.pdf"%(os.path.dirname(options.tfileName),os.path.basename(options.tfileName))).replace('.root',''))

if not options.includeVBF: nBind_vbf=0
if not options.includeVH:  nBind_vh=0

# can make a special "global toy" set of datacards
toymaker=0
if options.throwGlobalToy:
  	if not options.throwAsimov: toymaker = CombinedToyMaker(options.inputmassfacws)
  	else: toymaker = CombinedToyMaker("")	# Dont need mass-fact workspace for asimov cards
	if not options.inputpdfworkspace: 
		toymaker.createPdfs(options.treefilename,options.outputpdfworkspace,options.expSig)
	else:
		toymaker.loadPdfs(options.inputpdfworkspace,options.expSig)
	
	
	if not options.throwAsimov:
		toymaker.plotData(cardOutDir,160,200)
		toymaker.genData(cardOutDir+"/"+options.outputmassfactoy,options.expSig)
		toymaker.plotToy(cardOutDir,160,95,options.expSig)
		toymaker.saveToyWorkspace(cardOutDir+"/testToyWS.root")
	ROOT.gROOT.ProcessLine(".L python/tmvaLoader.C+")
	from ROOT import tmvaLoader
	g_tmva = tmvaLoader(options.tmvaweightsfolder+"/TMVAClassification_BDT%sMIT.weights.xml"%options.bdtType,options.bdtType)
  
# Now we can write the cards
tfile = ROOT.TFile(options.tfileName)
if options.singleMass>0: evalMasses=[float(options.singleMass)]
for m in evalMasses: 
	if options.throwGlobalToy: 
		#g_toydatalist=toymaker.returnWindowData(float(m),g_SIDEBANDWIDTH)
		if not options.throwAsimov: g_toydatalist=toymaker.returnWindowToyData(float(m),g_SIDEBANDWIDTH)
		if options.throwAsimov:
			g_toysiglist = toymaker.returnSignalAsimovData(float(m),g_SIDEBANDWIDTH)
		else:
			g_toydatalist=toymaker.returnWindowToyData(float(m),g_SIDEBANDWIDTH)
		#tagging of jets now implicitly taken car of in CombinedToyMaker
    #if options.includeVBF: tagPseudoDijets()
	#print toymaker.getN(m,0.02)
	writeCard(tfile,m,normG.Eval(m))
print "Done Writing Cards"


