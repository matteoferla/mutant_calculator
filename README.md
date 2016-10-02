# mutant_calculator
This app is available on [www.mutanalyst.com](http://www.mutanalyst.com).   
A full copy of the website, including third party tools (credits go to respective authors, _vide_ _infra_), can be found in my [dropbox](https://www.dropbox.com/sh/42b3ho1pqic67ej/AAAqmOBIC-Nzi4-7Xy5oDZKEa?dl=0), please note that the author (me) is not affiated with the third party tools.
If used please cite:   
> Ferla MP. Mutanalyst, an online tool for assessing the mutational spectrum of epPCR libraries with poor sampling.    
> BMC Bioinformatics. 2016 Apr 4;17:152.   
> * doi: [10.1186/s12859-016-0996-7](http://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-016-0996-7)
> * PubMed PMID: [27044645](https://www.ncbi.nlm.nih.gov/pubmed/27044645)
> * PubMed Central PMCID: [PMC4820924](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4820924/)

# Overview
This section details how the program works and its knowledge is not needed to use the program. It is intended as an overview in case a researcher wanted to alter it for a different purpose or copy a function from it.   
Mutanalysis is composed of three HTML pages:

* `Mutational_bias_calculator`
* `Mutation_counter`
*	`Variance_notes`

Each page uses a cetral CSS file, `mut.css`, and two external style resources, Font-Awesome and the Source Sans Pro (Google fonts), two commonly used resources used in contemporary webpages.

The three html pages also use several external JavaScript (JS) resources:

*	JQuery, an essential library that greatly simplifies JS coding.
*	Tooltip JS (and Tether JS and Drop JS, and its style sheet), a library used to make tootips (notes on hover), which have several advantages over the inbuilt title attribute of html tags.
*	Google Charts, a JS library that allows charts to be plotted, part of the Google Developers tool kit.
*	Google Analytics, a JS widget that send asynchronously data to Google allowing the author to see what browsers are being used. At present, Mutanalyst is optimally viewed with Google Chrome on a Mac or Windows, but that may change in the future.

Additionally the page `Mutational_counter.htm` uses a specific JS file, `mutationalCounter.js` while `Mutational_bias_calculator.htm` uses two specific JS files:

*	`mutationalBias.js`, a script that handles the calculations and does not interact with the document or utilise any other script.
*	`mutationalAux.js`, a script that handles all the events of the buttons and other document interactions.

The key object in the `mutationalBias.js` calculations is called “mutball” (following after tarball _etc._, a personal coding preference which I have [blogged about](http://blog.matteoferla.com/2015/11/how-shall-i-name-my-variables.html)), which store all the variables and contains several keys that match the id of elements in the html document allowing `mutationalAux.js` to modify them without unnecessary coding. Its constructor is called mutagen. With a few exceptions (radio buttons, which do not call `mutationalBias.js`) it is recreated in case the user alters anything. The exception get the object via SessionStorage. The attributes can additionally be passed by URL query string. Some of the attributes are:

*	`source`: a string noting whence the object was called.
*	`sequence`: _e.g._ ATATCGG.
*	`baseList`: _e.g._ G286A T306C A687T T880C\nWT\nWT.
*	`freqMean`: mean frequency of number of mutations per sequence, a simple arithmetic average.
*	`freqVar`: variance of number of mutations per sequence.
*	`freqList`: array of the mutation counts (binned) of the rows of baselist.
*	`freqΣ`: sum of number of mutations per sequence sampled.
*	`freqλ`: Poisson distribution of number of mutations per sequence.
*	`rawTable`: 4x4 nested arrays containing the mutation spectrum observed.
*	`mutTable`: as above but normalised.
*	`sumA`, vsumT` _etc._ the number of As in the sequence.
*	`A2T` _etc._ number of incidents going from A to T. There are 16 of these. It is redundant with rawTable: but for html reasons it’s repeated.
*	`size`: gene size in kb.
*	`TsOverTv` and `TsOverTv_error`: transitions over transversions and its error. The keys with errors are as follows (they codes are: W=weak AT, S=strong GC, N=any Σ=sum)
  *	`TsOverTv`
  *	`W2SOverS2W`
  *	`W2N`
  *	`S2N`
  *	`W2S`
  *	`S2W`
  *	`ΣTs`
  *	`Ts1`
  *	`Ts2`
  *	`ΣTv`
  *	`TvW`
  *	`TvN1`
  *	`TvS`
  *	`TvN2`

The main methods are:

*	`calcFreq(mutball)`: calculates the parameters associated with the number of mutations per sequence, in turn it calls various functions including fit(ordinate), which is a wrapper for the non-linear fitting fuction `fminsearch (fun,Parm0,x,y,Opt)`, passing it the function of the Poisson distribution —_i.e._ if you want to change function tinker with `fit()`. `fminsearch (fun,Parm0,x,y,Opt)` is a small function adapted from JMat (GNU licence)
*	`calcBias(mutball)`: calculates the mutational spectrum parameters.
*	`Mutagen()`: returns a blank mutball object.

So say one wanted to modify the script for personal use to calculate the _p_-value from a _t_-test against a given value and return it as an alert. One would have to find or write a _t_-test function and add it to a local copy of `mutationalBias.js`. Then to the end of `calcBias()` just before the return add an alert to pop up with the p-value. Parenthetically, whereas a normal distribution assumption is unavoidable due to the lack of data, it is not at all a good idea and is better to not hazard a guess of the probability, but to resort to other methods (_e.g._ if the value is within the error range there is no difference).


