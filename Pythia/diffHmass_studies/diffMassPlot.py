#!/usr/bin/env python
"""
Script to produce plots highlighting effect of changing H mass (125 vs ???)
"""

import ROOT
import os
from collections import namedtuple

ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(1)
ROOT.gStyle.SetLegendBorderSize(0)
ROOT.TH1.SetDefaultSumw2(True)

# files with TTrees
# 8 TeV
f_h125_ma4_8TeV = dict(file=ROOT.TFile('8TeV/ggh125_2a_4tau_ma1_4_8TeV_n50000.root'),
                       label='m_{H} = 125 GeV, m_{a} = 4 GeV, #sqrt{s} = 8 TeV',
                       color=ROOT.kBlack)
f_h125_ma8_8TeV = dict(file=ROOT.TFile('8TeV/ggh125_2a_4tau_ma1_8_8TeV_n50000.root'),
                       label='m_{H} = 125 GeV, m_{a} = 8 GeV, #sqrt{s} = 8 TeV',
                       color=ROOT.kBlue)
f_h300_ma4_8TeV = dict(file=ROOT.TFile('8TeV/ggh300_2a_4tau_ma1_4_8TeV_n50000.root'),
                       label='m_{H} = 300 GeV, m_{a} = 4 GeV, #sqrt{s} = 8 TeV',
                       color=ROOT.kRed)
f_h300_ma8_8TeV = dict(file=ROOT.TFile('8TeV/ggh300_2a_4tau_ma1_8_8TeV_n50000.root'),
                       label='m_{H} = 300 GeV, m_{a} = 8 GeV, #sqrt{s} = 8 TeV',
                       color=ROOT.kGreen+3)
# 13 TeV
f_h125_ma4_13TeV = dict(file=ROOT.TFile('13TeV/ggh125_2a_4tau_ma1_4_13TeV_n50000.root'),
                        label='m_{H} = 125 GeV, m_{a} = 4 GeV, #sqrt{s} = 13 TeV',
                        color=ROOT.kBlack)
f_h125_ma8_13TeV = dict(file=ROOT.TFile('13TeV/ggh125_2a_4tau_ma1_8_13TeV_n50000.root'),
                        label='m_{H} = 125 GeV, m_{a} = 8 GeV, #sqrt{s} = 13 TeV',
                        color=ROOT.kBlue)
f_h300_ma4_13TeV = dict(file=ROOT.TFile('13TeV/ggh300_2a_4tau_ma1_4_13TeV_n50000.root'),
                        label='m_{H} = 300 GeV, m_{a} = 4 GeV, #sqrt{s} = 13 TeV',
                        color=ROOT.kRed)
f_h300_ma8_13TeV = dict(file=ROOT.TFile('13TeV/ggh300_2a_4tau_ma1_8_13TeV_n50000.root'),
                        label='m_{H} = 300 GeV, m_{a} = 8 GeV, #sqrt{s} = 13 TeV',
                        color=ROOT.kGreen+3)

# Handy structure to hold info about a plot
Plot = namedtuple('Plot', 'tree var nbins xlim xtitle ytitle title')

# some common axis limits & binning
phi_xlim, phi_nbins = [-ROOT.TMath.Pi(), ROOT.TMath.Pi()], 25
eta_xlim, eta_nbins = [-5, 5], 40
dphi_xlim, dphi_nbins = [0, ROOT.TMath.Pi()], 50
dr_xlim, dr_nbins = [0, 2 * ROOT.TMath.Pi()], 50
dphi_xlim_small, dphi_nbins_small = [0, 0.5], 50
dr_xlim_small, dr_nbins_small = [0, 0.5], 50

# Declare the plot you wnat here
plots = [
    # h1 vars
    Plot(tree='hVars', var='hPt', nbins=50, xlim=[0, 200],
         xtitle='H p_{T} [GeV]', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    Plot(tree='hVars', var='hEta', nbins=eta_nbins, xlim=eta_xlim,
         xtitle='H #eta', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    Plot(tree='hVars', var='hPhi', nbins=phi_nbins, xlim=phi_xlim,
         xtitle='H #phi [rads]', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    Plot(tree='hVars', var='a1DPhi', nbins=dphi_nbins, xlim=dphi_xlim,
         xtitle='#Delta #phi(a_{1}, a_{1}) [rads]', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    Plot(tree='hVars', var='a1Dr', nbins=dr_nbins, xlim=dr_xlim,
         xtitle='#Delta R(a_{1}, a_{1}) [rads]', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    # a1 vars
    Plot(tree='a1Vars', var='a1Pt', nbins=100, xlim=[0, 400],
         xtitle='a_{1} p_{T} [GeV]', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    Plot(tree='a1Vars', var='a1Eta', nbins=eta_nbins, xlim=eta_xlim,
         xtitle='a_{1} #eta', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    Plot(tree='a1Vars', var='a1Phi', nbins=phi_nbins, xlim=phi_xlim,
         xtitle='a_{1} #phi [rads]', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    Plot(tree='a1Vars', var='a1DecayDPhi', nbins=dphi_nbins_small, xlim=dphi_xlim_small,
         xtitle='#Delta #phi(#tau, #tau) [rads]', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    Plot(tree='a1Vars', var='a1DecayDr', nbins=dr_nbins_small, xlim=dr_xlim_small,
         xtitle='#Delta R(#tau, #tau)', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    # a1 decay vars (i.e. tau or b)
    Plot(tree='a1DecayVars', var='a1DecayPt', nbins=100, xlim=[0, 400],
         xtitle='#tau p_{T} [GeV]', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    Plot(tree='a1DecayVars', var='a1DecayEta', nbins=eta_nbins, xlim=eta_xlim,
         xtitle='#tau #eta', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    Plot(tree='a1DecayVars', var='a1DecayPhi', nbins=phi_nbins, xlim=phi_xlim,
         xtitle='#tau #phi [rads]', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level)'),
    # vars for mu from a1 decay with cuts on 2 SS mu
    Plot(tree='a1DecayMuVars', var='a1DecayMuPt', nbins=50, xlim=[0, 100],
         xtitle='#mu_{#tau} p_{T} [GeV]', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level), require #geq 2 SS #mu'),
    Plot(tree='a1DecayMuVars', var='a1DecayMuEta', nbins=eta_nbins, xlim=eta_xlim,
         xtitle='#mu_{#tau} #eta', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level), require #geq 2 SS #mu'),
    Plot(tree='a1DecayMuVars', var='a1DecayMuPhi', nbins=phi_nbins, xlim=phi_xlim,
         xtitle='#mu_{#tau} #phi [rads]', ytitle='p.d.f.',
         title='ggH #rightarrow 2a #rightarrow 4#tau (Gen. level), require #geq 2 SS #mu'),
]


def normalise(h):
    """Normalise histogram such that integral = 1"""
    h.Scale(1./h.Integral())


def plot_compare(file_1, file_2, plot, plot_dir, oFormat='pdf'):
    """Plot histogram from file_1 and file_2 on same canvas and save.

    file_1, file_2: dict
        Dict of information about files, including filename, label (for legend),
        and color (for histograms).
    plot: Plot namedtuple
        Information about histogram plotting options, including x & y
        axis titles, overall title, rebin value, and x-axis limit (if desired).
    plot_dir: str
        Directory in which to save plots
    oFormat: Optional[str]
        Output format for plot files.
    """
    unique_name = '%s_%s' % (plot_dir.replace("/", "_"), plot.var)
    c = ROOT.TCanvas("c_%s" % unique_name, '', 800, 600)
    c.SetTicks(1, 1)

    hst = ROOT.THStack('hst_%s' % unique_name, plot.title)
    leg = ROOT.TLegend(0.45, 0.7, 0.85, 0.88)
    leg.SetFillStyle(0)

    h_title = ';'.join([plot.title, plot.xtitle, plot.ytitle])
    for i, f in enumerate([file_1, file_2]):
        # Get required TTree, fill hist
        tree = f['file'].Get(plot.tree)
        if not tree:
            print 'No tree %s in file %s' % (plot.tree, f['file'])
            exit(1)
        h_name = '%s_%d' % (unique_name, i)
        h = ROOT.TH1D(h_name, h_title, plot.nbins, plot.xlim[0], plot.xlim[1])
        tree.Draw('%s>>%s' % (plot.var, h_name), "", "")
        h.SetLineColor(f['color'])
        normalise(h)
        hst.Add(h)
        leg.AddEntry(h, f['label'],"L")
    hst.Draw('NOSTACK HISTE')
    leg.Draw()
    h_draw = hst.GetHistogram()
    h_draw.GetXaxis().SetTitleOffset(1.1)
    h_draw.GetYaxis().SetTitleOffset(1.3)
    h_draw.SetTitle(h_title)
    # Save to PDF
    if not os.path.isdir(plot_dir):
        os.makedirs(plot_dir)
    c.SaveAs('%s/%s.%s' % (plot_dir, plot.var, oFormat))


if __name__ == "__main__":
    for hist in plots:
        # 8TeV
        # plot ma = 4, various mH
        plot_compare(f_h125_ma4_8TeV, f_h300_ma4_8TeV, hist, '8TeV/mh125vs300_ma4')
        # plot ma = 8, various mH
        plot_compare(f_h125_ma8_8TeV, f_h300_ma8_8TeV, hist, '8TeV/mh125vs300_ma8')
        # plot mH = 125, various ma
        plot_compare(f_h125_ma4_8TeV, f_h125_ma8_8TeV, hist, '8TeV/mh125_ma4vs8')
        # plot mH = 300, various ma
        plot_compare(f_h300_ma4_8TeV, f_h300_ma8_8TeV, hist, '8TeV/mh300_ma4vs8')

        # 13 TeV
        # plot ma = 4, various mH
        plot_compare(f_h125_ma4_13TeV, f_h300_ma4_13TeV, hist, '13TeV/mh125vs300_ma4')
        # plot ma = 8, various mH
        plot_compare(f_h125_ma8_13TeV, f_h300_ma8_13TeV, hist, '13TeV/mh125vs300_ma8')
        # plot mH = 125, various ma
        plot_compare(f_h125_ma4_13TeV, f_h125_ma8_13TeV, hist, '13TeV/mh125_ma4vs8')
        # plot mH = 300, various ma
        plot_compare(f_h300_ma4_13TeV, f_h300_ma8_13TeV, hist, '13TeV/mh300_ma4vs8')

