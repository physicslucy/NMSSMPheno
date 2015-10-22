#!/usr/bin/env python
"""
Script to produce plots highlighting effect of changing H mass (125 vs ???)
"""

import ROOT
import os

ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(1)
ROOT.gStyle.SetLegendBorderSize(0)
ROOT.TH1.SetDefaultSumw2(True)


f_h125_ma4 = dict(file=ROOT.TFile('ggh125_2a_4tau_ma1_4_n50000.root'),
                  label='m_{H} = 125 GeV, m_{a} = 4 GeV',
                  color=ROOT.kBlack)
f_h125_ma8 = dict(file=ROOT.TFile('ggh125_2a_4tau_ma1_8_n50000.root'),
                  label='m_{H} = 125 GeV, m_{a} = 8 GeV',
                  color=ROOT.kBlue)
f_h300_ma4 = dict(file=ROOT.TFile('ggh300_2a_4tau_ma1_4_n50000.root'),
                  label='m_{H} = 300 GeV, m_{a} = 4 GeV',
                  color=ROOT.kRed)
f_h300_ma8 = dict(file=ROOT.TFile('ggh300_2a_4tau_ma1_8_n50000.root'),
                  label='m_{H} = 300 GeV, m_{a} = 8 GeV',
                  color=ROOT.kGreen+3)

hist_names = {"hPt": dict(xtitle='H p_{T} [GeV]', ytitle='p.d.f.', title='ggH #rightarrow 2a #rightarrow 4#tau', rebin=4, xlim=None),
              "a1Pt": dict(xtitle='a_{1} p_{T} [GeV]', ytitle='p.d.f.', title='ggH #rightarrow 2a #rightarrow 4#tau', rebin=4, xlim=None),
              "a1Eta": dict(xtitle='a_{1} #eta', ytitle='p.d.f.', title='ggH #rightarrow 2a #rightarrow 4#tau', rebin=10, xlim=None),
              "a1Dr": dict(xtitle='#DeltaR(a_{1}, a_{1})', ytitle='p.d.f.', title='ggH #rightarrow 2a #rightarrow 4#tau', rebin=10, xlim=None),
              "a1DecayDr": dict(xtitle='#DeltaR(#tau, #tau)', ytitle='p.d.f.', title='ggH #rightarrow 2a #rightarrow 4#tau', rebin=1, xlim=[0, 0.5]),
              "a1DecayPt": dict(xtitle='#tau p_{T} [GeV]', ytitle='p.d.f.', title='ggH #rightarrow 2a #rightarrow 4#tau', rebin=4, xlim=[0, 300]),
              "a1MuPt": dict(xtitle='#mu_{#tau} p_{T} [GeV]', ytitle='p.d.f.', title='ggH #rightarrow 2a #rightarrow 4#tau', rebin=4, xlim=None),
              "a1MuEta": dict(xtitle='#mu_{#tau} #eta', ytitle='p.d.f.', title='ggH #rightarrow 2a #rightarrow 4#tau', rebin=10, xlim=None),
              }


def normalise(h):
    """Normalise histogram such that integral = 1"""
    h.Scale(1./h.Integral())


def plot_compare(file_1, file_2, h_name, h_opts, plot_dir):
    """Plot histogram from file_1 and file_2 on same canvas and save.

    file_1, file_2: dict
        Dict of information about files, including filename, label (for legend),
        and color (for histograms).
    h_name: str
        Name of histogram in ROOT files to plot. Must be the same in both files.
    h_opts: dict
        Dict of information about histogram plotting options, including x & y
        axis titles, overall titile, rebin value, and x-axis limit (if desired).
    plot_dir: str
        Directory in which to save plots
    """
    c = ROOT.TCanvas("c_%s_%s" % (plot_dir, h_name), '', 800, 600)
    c.SetTicks(1, 1)

    hst = ROOT.THStack('hst_%s_%s' % (plot_dir, h_name), h_opts['title'])
    # have to set plot title here, not below for some stupid reason
    leg = ROOT.TLegend(0.56, 0.7, 0.85, 0.88)
    leg.SetFillStyle(0)

    h_1 = file_1['file'].Get(h_name).Clone('%s_%s' % (plot_dir, h_name))
    h_2 = file_2['file'].Get(h_name).Clone('%s_%s' % (plot_dir, h_name))
    for h, f in zip([h_1, h_2], [file_1, file_2]):
        h.SetLineColor(f['color'])
        h.Rebin(h_opts['rebin'])
        normalise(h)
        hst.Add(h)
        leg.AddEntry(h, f['label'],"L")
    hst.Draw('NOSTACK')
    leg.Draw()
    h_draw = hst.GetHistogram()
    h_draw.SetTitle(';'.join(['', h_opts['xtitle'], h_opts['ytitle']]))
    h_draw.GetXaxis().SetTitleOffset(1.1)
    h_draw.GetYaxis().SetTitleOffset(1.3)
    if h_opts['xlim']:
        h_draw.SetAxisRange(h_opts['xlim'][0], h_opts['xlim'][1], 'X')
    if not os.path.isdir(plot_dir):
        os.makedirs(plot_dir)
    c.SaveAs('%s/%s.pdf' % (plot_dir, h_name))


for h_name, h_opts in hist_names.iteritems():

    # plot ma = 4, various mH
    plot_compare(f_h125_ma4, f_h300_ma4, h_name, h_opts, 'mh125vs300_ma4')

    # plot ma = 8, various mH
    plot_compare(f_h125_ma8, f_h300_ma8, h_name, h_opts, 'mh125vs300_ma8')

    # plot mH = 125, various ma
    plot_compare(f_h125_ma4, f_h125_ma8, h_name, h_opts, 'mh125_ma4vs8')

    # plot mH = 300, various ma
    plot_compare(f_h300_ma4, f_h300_ma8, h_name, h_opts, 'mh300_ma4vs8')

