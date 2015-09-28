"""
Simple scirpt to plot DeltaR distributions from files
"""
import ROOT
from collections import OrderedDict

ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(1)

files = OrderedDict()
files["hist_a1a1_20.root"] = dict(color=ROOT.kRed, linestyle=1)
files["hist_a1a1_30.root"] = dict(color=ROOT.kBlue, linestyle=1)
files["hist_a1a1_40.root"] = dict(color=ROOT.kMagenta, linestyle=1)
files["hist_a1a1_50.root"] = dict(color=ROOT.kGreen+2, linestyle=1)
files["hist_a1a1_60.root"] = dict(color=ROOT.kOrange, linestyle=1)
files["hist_a1a1_70.root"] = dict(color=ROOT.kViolet+7, linestyle=1)
files["hist_a1a1_80.root"] = dict(color=ROOT.kBlack, linestyle=1)

stack = ROOT.THStack("stack","h(450) #rightarrow a1a1, a1 #rightarrow b#bar{b};#Delta R(bb);p.d.f.");
leg = ROOT.TLegend(0.6, 0.55, 0.88, 0.88)
leg.SetLineWidth(0)
leg.SetLineColor(0)

for i, (fname, settings) in enumerate(files.items()):
    mass = fname.replace("hist_a1a1_", "").replace(".root", "")

    f = ROOT.TFile(fname)
    if not f:
        print "cannot open", fname
        continue

    h = f.Get("bbDr").Clone("h"+mass)
    if not h:
        print "cannot get hist"
        continue

    h.SetLineColor(settings['color'])
    h.SetFillColorAlpha(settings['color'], 0.55)
    h.SetLineStyle(settings['linestyle'])
    h.Scale(1./h.Integral())
    h.SetAxisRange(0, 1.5, 'X')
    h.SetDirectory(0)  # VERY IMPORTANT otherwise TFile owns hist
    stack.Add(h)
    leg.AddEntry(h, "m_{a1} = %s GeV " % mass, "LF")
    f.Close()


c = ROOT.TCanvas("c", "", 800, 800)
c.SetTicks(1,1)
stack.Draw("NOSTACK")
leg.Draw()
master = stack.GetHistogram()
master.SetAxisRange(0, 1.5, 'X')
master.SetTitle("h(450) #to a1a1, a1 #to b;#Delta R(bb);p.d.f.")
c.SaveAs("a1a1_dr.pdf")
