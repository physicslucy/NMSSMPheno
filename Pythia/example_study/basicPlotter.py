#!/usr/bin/env python

"""
This is a basic PyROOT script designed to showoff features of Python and PyROOT.
It runs over a ROOT file as output by generateMC.exe

You can run it either as:

python basicPlotter.py <ROOT file>

or since it's an executable:

./basicPlotter.py <ROOT file>

The triple quotes mark a 'block comment'

Also I try to keep lines to about ~80 characters long. Makes things more
readable on a small screen, and allows for side-by-side windows.
"""


# Here we load both standard and third-party packages.
import sys  # allows us to get any commandline options
import ROOT


# ROOT likes to screw up the user's arguments, stop this:
ROOT.PyConfig.IgnoreCommandLineOptions = True
# Run ROOT in batch mode to stop opening a load of windows
ROOT.gROOT.SetBatch(1)
# Set what you want to see in the info box on a plot. 0 is off.
ROOT.gStyle.SetOptStat(0)
# This ensures errors are correctly handled when adding/multiplying histograms
ROOT.TH1.SetDefaultSumw2(True)


# This is a function (aka method). Don't forget the colon!
def make_easy_plot(filename, fmt='pdf'):
    """
    This is a docstring. It is meant to describe the method, its arguments,
    and any returns.

    Anyway, this is a simple variable -> histogram function to show how easy
    it is to plot from a tree.

    filename: str
        Name of file to be processed.
    fmt: str
        Output file format for plots. Here we have specified a default argument,
        so that the user doesn't have to supply one (the defualt should be ok!)
    """

    # Open a ROOT file by creating a TFile object, assign to variable named rf.
    # We dont' need to write to it, so we open it in READ mode.
    #
    # (NB unlike normal python, we can't do 'with open(...) as f: I'm afraid)
    rf = ROOT.TFile(filename, 'READ')

    # Check the file is ok. If the file didn't open, rf will be set to None.
    # none always evaulates False, so "not None" will be True.
    # Note that ROOT is perfectly happy to open a file that doesn't exist...!
    if not rf:
        # We've used variable substituion here, like in C's printf().
        # s for strings, d for integers, f for floats...
        raise RuntimeError('Cannot open file %s', filename)

    # Print things to screen. The comma acts as a concatenator (with an extra space)
    print 'Processing', filename

    # Get the TTree object inside the file. We do this using its name,
    # which we've stored in a string variable.
    tree_name = 'hVars'
    tree = rf.Get(tree_name)

    # Check it actually got it ok, since ROOT will happily Get() an object that
    # doesn't exist (and from a file that doesn't exist!)
    if not tree:
        raise RuntimeError('Cannot get tree %s' % tree_name)

    # We need a TCanvas to plot things on. ROOT does create one automatically,
    # but we want to have extra control.
    # The arguments are:
    # - object name in the ROOT ecosystem. Note this is INDEPENDENT of its
    # variable name (canv). ROOT likes to keep track of EVERY ROOT object that
    # gets created/used, and it does this using the object name.
    # - the canvas title
    # - the width (in pixels)
    # - the height (in pixels)
    canv = ROOT.TCanvas('c1', 'My First Plot', 800, 600)

    # This is the easiest and fastest way to plot variables stored in TTree branches
    # (But only works so long as the variable exists in the TTree)
    #
    # We first create a 1D histogram object. Yes, ROOT does also do this
    # automatically, but we want control over it.
    #
    # Arguments:
    # - object name. Same caveat as earlier.
    # - histogram title. Will be displayed on the plot. We can also take this
    # opportunity to define the x and y axis titles. This is done by using
    # semi-colons to split it into <title>;<x axis title>;<y axis title>
    # Also note you can do Latex-y stuff!
    # - number of bins (spaced equidistantly)
    # - lower edge of binning
    # - upper edge of binning
    hist_pt = ROOT.TH1F('histPt', "My First Histogram;h p_{T} [GeV];N", 25, 0, 100)

    # This says "draw variable 'hPt' in TTree 'tree' to a histogram object named "histPt"
    # YOU MUST USE THE ROOT OBJECT NAME, not the python variable name!
    # So it's "histPt" NOT hist_pt
    #
    # It draws it onto our canvas 'canv', since that was the last canvas defined
    # (some ROOT voodoo going on there)
    #
    # The middle argument is a selection string, we'll deal with this later.
    # The last argument are drawing options, see documentation for THistPainter.
    # HISTE draws the outline fo the histogram with error bars.
    tree.Draw("hPt>>histPt", "", "HISTE")

    # Save it to file.
    # We have to save the canvas, not the histogram
    canv.SaveAs('what_a_fantastic_first_plot.%s' % fmt)

    # Close the file object
    rf.Close()


def make_easy_2d_plot(filename, fmt='pdf'):
    """
    Do some 2D plotting.

    filename: str
        Name of file to be processed.
    fmt: str
        Output file format for plots.
    """

    # same stuff as before...
    rf = ROOT.TFile(filename, 'READ')
    if not rf:
        raise RuntimeError('Cannot open file %s', filename)

    tree_name = 'a1Vars'
    tree = rf.Get(tree_name)
    if not tree:
        raise RuntimeError('Cannot get tree %s' % tree_name)
    canv = ROOT.TCanvas('c1', 'My Second Plot', 800, 600)

    # Let's investigate a correlation.
    # To do this we need a 2D histogram, or a "heat map".
    # We need to specify a different histogram object to before.
    # Note that it's similar to before but:
    # - in the title string we have an extra field - can label the Z axis
    # - we have to specify number of Y bins, lower Y edge, upper Y edge as well
    h2d_pt = ROOT.TH2F('h2d',
                       "2D hist;a_{1} p_{T} [GeV];a_{1} decay products #DeltaR;N",
                       50, 0, 100, 35, 0, 3.5)

    # The draw syntax allows us to easily do a 2D plot.
    # IMPORTANT the order of variables is <y>:<x>, bit counterintuitve.
    # The COL tells ROOT to represent bin contents using colours, and Z adds a
    # colourbar to show which colour maps to what value.
    tree.Draw("a1DecayDr:a1Pt>>h2d", "", "COLZ")

    canv.SaveAs('a_stunning_2d_plot.' + fmt)  # it's real easy to concatenate strings

    rf.Close()


def make_harder_plot(filename, fmt='pdf'):
    """
    Do some more plotting.

    filename: str
        Name of file to be processed.
    fmt: str
        Output file format for plots.
    """

    # same stuff as before...
    rf = ROOT.TFile(filename, 'READ')
    if not rf:
        raise RuntimeError('Cannot open file %s', filename)

    tree_name = 'hVars'
    tree = rf.Get(tree_name)
    if not tree:
        raise RuntimeError('Cannot get tree %s' % tree_name)

    canv = ROOT.TCanvas('c1', 'My Second Plot', 800, 600)
    canv.SetTicks(1)  # add in ticks on upper X axis and right Y axis

    # Let's do something more complex.
    # Imagine we want to plot the pT of Higgs bosons, but split according to
    # whether they were produced in the central region (|eta| < 2.4) or in
    # the forward region (|eta| > 2.4).
    #
    # We'll create a histogram for each, then plot them on the same canvas.
    #
    # First setup the histograms to be filled:
    h_pt_central = ROOT.TH1F('h_cen', ";h p_{T} [GeV];N", 25, 0, 100)
    h_pt_forward = ROOT.TH1F('h_fwd', ";h p_{T} [GeV];N", 25, 0, 100)

    # The draw syntax allows us to easily draw with selection requirements.
    # This is the mysterious middle argument!
    # We can use any variable in the tree to create a 'cut string',
    # and even do maths and logic in there!
    # The SAME means draw onto the xisting canvas WITHOUT clearing it first.
    # If we don't use SAME, the canvas gets cleared each time Draw() is called.
    fwd_boundary = 2.4
    tree.Draw("hPt>>h_cen", "TMath::Abs(hEta) < %f" % fwd_boundary, "HISTE")
    tree.Draw("hPt>>h_fwd", "TMath::Abs(hEta) > %f" % fwd_boundary, "HISTESAME")

    # We can save the result, but it isn't very impressive...
    canv.SaveAs('complicated_plot.' + fmt)

    # Give the hists different stylings
    h_pt_central.SetLineColor(ROOT.kBlack)  # ROOT has a number of builtin colors, most of which suck.
    h_pt_forward.SetLineColor(ROOT.kBlue)
    h_pt_forward.SetLineStyle(2)

    # Let's normalise our histograms, so that their integral = 1.
    h_pt_central.Scale(1. / h_pt_central.Integral())
    h_pt_forward.Scale(1. / h_pt_forward.Integral())

    # There's a ROOT container to handle multiple histograms, THStack.
    # It's really handy for auto-ranging the Y axis to account for the min/max
    # of all bins in all component histograms.
    # We add our histograms to it AFTER any styling.
    # Also note we have to re-specufy the X and Y axis titles.
    stack = ROOT.THStack("hstack", "stack title;h p_{T} [GeV]; p.d.f")
    stack.Add(h_pt_central)
    stack.Add(h_pt_forward)

    # THStack can be drawn like a noraml histogram. We also add the option NOSTACK
    # to avoid plotting ths histograms cumulatively
    stack.Draw("NOSTACK HISTE")

    # Add a legend to the plot
    # The arguments are its position onscreen, with (0, 0) being bottom left,
    # and (1, 1) is top right.
    leg = ROOT.TLegend(0.67, 0.69, 0.87, 0.87)
    leg.AddEntry(h_pt_central, "|#eta_{h}| < %.1f" % fwd_boundary, "L")
    leg.AddEntry(h_pt_forward, "|#eta_{h}| > %.1f" % fwd_boundary, "L")
    leg.SetLineWidth(0)
    leg.Draw()  # needed otherwise the legend won't turn up!

    canv.SaveAs('complicated_plot_better.' + fmt)

    rf.Close()


def print_tree_vars(filename):
    """
    Sometimes we need to loop through each entry in a tree.

    This is how.
    """
    rf = ROOT.TFile(filename, 'READ')
    if not rf:
        raise RuntimeError('Cannot open file %s', filename)

    tree_name = 'a1Vars'
    tree = rf.Get(tree_name)
    if not tree:
        raise RuntimeError('Cannot get tree %s' % tree_name)

    # It's this easy. Exactly like iterating through a list.
    # We use enumerate() to count the entry as we go, with 'ind' starting at 0.
    # enumerate() returns 2 objects - the index, and the matching result from
    # iterating over the argument.
    # So here entry is a leaf (entry) in the Branch.
    for ind, entry in enumerate(tree):
        if ind == 10:
            break

        print "Entry", ind, ":: "

        # We can also use our standard string formatters.
        # The \t here is a printable tab character.
        # We can do maths with our tree variables!
        print "\ta1 pt = %.3f, a1 phi(degrees) = %.3f" % (entry.a1Pt,
                                                          entry.a1Phi * 180. / ROOT.TMath.Pi())

    rf.Close()


if __name__ == "__main__":
    """
    This part only runs if script is executed.

    If we import it into another script, this bit won't run.
    """

    # sys.argv is a list of all the user's command line arguments
    # The first one is the program name.
    # The second argument will be the ROOT filename.
    # len() counts the size of iterable things like lists
    if len(sys.argv) != 2:
        raise RuntimeError("Need to speicfy 1 filename to process")

    make_easy_plot(sys.argv[1])  # [1] means 'get the 2nd element', since the first is at [0]
    make_easy_2d_plot(filename=sys.argv[1], fmt='png')  # We can use the argument name when calling it! Make things SO much clearer
    make_harder_plot(sys.argv[1])
    print_tree_vars(sys.argv[1])
