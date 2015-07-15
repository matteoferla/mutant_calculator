//**************************************************
//the mutball object.
//Commit and read were initially written as methods of mutball, but were moved out in order to quarantine interactions with document to the document.
//The single letter codes (A, C, T, G, S, W, N and so forth are the normal ones. see https://en.wikipedia.org/wiki/Nucleic_acid_notation if unfamiliar. Ts transition, Tv transversion. 
function mutagen() {
    var mutball = {
        source: "load",
        sequence: "",
        baseList: "",
        freqMean: "N/A",
        freqVar: "N/A",
        freqList: "N/A",
        mutTable: [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ],
        types: ['TsOverTv', 'W2SOverS2W', 'W2N', 'S2N', 'W2S', 'S2W', 'ΣTs', 'Ts1', 'Ts2', 'ΣTv', 'TvW', 'TvN1', 'TvS', 'TvN2']
    }
    for (b in bases) {
        mutball["sum" + bases[b]] = "25";
    }
    for (b in ways) {
        mutball[ways[b]] = "0";
    }
    return mutball;
}

//**********************************
//Math fnxs
function variance(values) {
    var avg = average(values);
    var squareDiffs = values.map(function(value) {
        var diff = value - avg;
        return diff * diff;
    });
    return average(squareDiffs);
}

function average(data) {
    var sum = data.reduce(function(sum, value) {
        return sum + value;
    }, 0);
    return sum / data.length;
}

function rd(x) {
    return Math.round(x * 10) / 10;
}

function transSum(m, x, y, w, z) {
    var s = m[x][y] + m[w][z];
    var v = variance([m[x][y], m[w][z]]);
    var d = Math.sqrt(v / 2);
    return [s, d, v];
}

function varRatio(mx, vx, my, vy, n) {
    var mxsq = Math.pow(mx, 2);
    var mysq = Math.pow(my, 2);
    var mxqd = Math.pow(mx, 4);
    return Math.abs(vy / mxsq + mysq * vx / mxqd) / n; //covariance set to 0.
}

function qV(m, x, y) {
    return variance([m[x][y], m[y][x]]);
}

function fit(ordinate) {
    //ordinate=mutball.freqList;
    abscissa = [];
    s = ordinate.reduce(function(a, b) {
        return a + b;
    }); //And this is why JS is a pain.
    //load underscore range? Nah, I need to fix blanks and normalise
    for (n = 0; n < ordinate.length; n++) {
        ordinate[n] = ordinate[n] / s || 0;
        abscissa[n] = n;
    }
    //
    //Math.factorial() does not call. http://mathjs.org/docs/reference/functions/factorial.html says it should.
    poisson = function(x, P) {
        λ = P[0];
        return x.map(function(xi) {
            function factorial(n) {
                if (n == 0) {
                    return 1
                } else if (n == 1) {
                    return 1
                } else {
                    return n-- * factorial(n)
                }
            }
            return Math.pow(λ, xi) * Math.exp(-λ) / factorial(xi)
        })
    }
    return jmat.fminsearch(poisson, [0.5], abscissa, ordinate);
}

//Major fnxs

function calcFreq(mutball) {
    //mutball = mutball || mutagen().read(["sequence","baseList"]);
    //parse sequence
    var seq = mutball.sequence.replace(/[^ATGC]/g, '').split('');
    var freq = {
        'A': 0,
        'C': 0,
        'G': 0,
        'T': 0
    };
    for (var x = 0; x < seq.length; x++) {
        freq[seq[x]]++;
    }
    for (var x = 0; x < 4; x++) {
        mutball["sum" + bases[x]] = Math.round(freq[bases[x]] / seq.length * 1000) / 10;
    }
    //parse mutants
    var tally = [];
    var raw_list = mutball.baseList.split(/\r\n|\r|\n/g);
    for (var i = 0; i < raw_list.length; i++) {
        if (!raw_list[i].match(/\w/)) {
            continue;
        }
        var variant = raw_list[i].split(/\W/g);
        if ((variant[0] == 'WT') || (variant[0] == 'wt')) {
            tally[i] = 0;
            continue;
        }
        tally[i] = variant.length;
        for (var j = 0; j < variant.length; j++) {
            mutball[variant[j].substr(0, 1) + "2" + variant[j].substr(-1, 1)]++;
        }
    }
    mutball.freqMean = Math.round(average(tally) * 10) / 10;
    mutball.freqVar = Math.round(variance(tally) * 10) / 10;

    var pivot = []; //can't remember the fancy trick to make a counter
    for (var j = 0; j < tally.length; j++) {
        pivot[tally[j]] = pivot[tally[j]] || 0;
        pivot[tally[j]]++;
    }
    for (var j = 0; j < pivot.length; j++) { //copypaste fix. clean needed.
        pivot[j] = pivot[j] || 0;
    }
    mutball.freqList = pivot.map(function(x) {
        return x
    }); //deref and re-ref.
    mutball.freqλ = rd(fit(pivot) * 10) / 10;
    mutball.source = "freq";
    return mutball;
}

function calcBias(mutball) {
    //mutball = mutball || mutagen().read(ways.concat(["sumA","sumT","sumG","sumC"]));
    //Get data
    var Amuts = ["A2A", "A2T", "A2G", "A2C"].map(function(x) {
        return mutball[x]
    });
    var Tmuts = ["T2A", "T2T", "T2G", "T2C"].map(function(x) {
        return mutball[x]
    });
    var Gmuts = ["G2A", "G2T", "G2G", "G2C"].map(function(x) {
        return mutball[x]
    });
    var Cmuts = ["C2A", "C2T", "C2G", "C2C"].map(function(x) {
        return mutball[x]
    });
    var muts = [Amuts, Tmuts, Gmuts, Cmuts];
    var dis = ["sumA", "sumT", "sumG", "sumC"].map(function(x) {
        return mutball[x]
    });;

    //Normalise
    var summa = 0;
    for (i = 0; i < 4; i++) {
        for (j = 0; j < 4; j++) {
            muts[i][j] /= dis[i];
            summa += muts[i][j];
        }
    }
    summa /= 100; // /100 --> %
    for (i = 0; i < 4; i++) {
        for (j = 0; j < 4; j++) {
            muts[i][j] /= summa;
        }
    }
    mutball.mutTable = muts;

    //Canculate fancy table

    //A>G + T>C
    var Ts1 = transSum(muts, A, G, T, C);

    //G>A + C>T
    var Ts2 = transSum(muts, G, A, C, T);

    //Ts total
    //As of ECMA 5, unicode variables you say?
    var ΣTs = [];
    ΣTs[0] = Ts1[0] + Ts2[0];
    ΣTs[2] = Ts1[2] + Ts2[2]; //Biename for variance.
    ΣTs[1] = Math.sqrt(ΣTs[2] / 2); // n  is 2

    //A>T + T>A
    var TvW = transSum(muts, A, T, T, A);

    //A&#8594;C, T&#8594;G
    var TvN1 = transSum(muts, A, C, T, G);

    // G&#8594;C, C&#8594;G
    var TvS = transSum(muts, G, C, C, G);

    // G&#8594;T, C&#8594;A
    var TvN2 = transSum(muts, G, T, C, A);

    //Tv total
    var ΣTv = [];
    ΣTv[0] = TvW[0] + TvS[0] + TvN1[0] + TvN2[0];
    ΣTv[2] = TvW[2] + TvS[2] + TvN1[2] + TvN2[2]; //Biename for variance.
    ΣTv[1] = Math.sqrt(ΣTv[2] / 4); // n =4

    //Ts/Tv
    var TsOverTv = [];
    TsOverTv[0] = ΣTs[0] / ΣTv[0];
    TsOverTv[2] = varRatio(ΣTs[0], ΣTs[2], ΣTv[0], ΣTv[2], 2); // Taylor w n =2
    TsOverTv[1] = Math.sqrt(TsOverTv[2] / 2);

    //AT&#8594;GC
    var W2S = [];
    W2S[0] = muts[A][G] + muts[A][C] + muts[T][G] + muts[T][C];
    W2S[2] = variance([muts[A][G], muts[T][C]]) + variance([muts[A][C], muts[T][G]]);
    W2S[1] = Math.sqrt(W2S[2] / 2);

    //GC&#8594;AT
    var S2W = [];
    S2W[0] = muts[G][A] + muts[G][T] + muts[C][A] + muts[C][T];
    S2W[2] = variance([muts[G][A], muts[C][T]]) + variance([muts[G][T], muts[C][A]]);
    S2W[1] = Math.sqrt(S2W[2] / 2);

    //AT&#8594;GC/GC&#8594;AT
    var W2SOverS2W = [];
    W2SOverS2W[0] = W2S[0] / S2W[0];
    W2SOverS2W[2] = varRatio(W2S[0], W2S[2], S2W[0], S2W[2], 2);
    W2SOverS2W[1] = Math.sqrt(W2SOverS2W[2] / 2);

    ////AT&#8594;GC/GC&#8594;AT
    var W2SOverS2W = [];
    W2SOverS2W[0] = W2S[0] / S2W[0];
    W2SOverS2W[2] = varRatio(W2S[0], W2S[2], S2W[0], S2W[2], 2);
    W2SOverS2W[1] = Math.sqrt(W2SOverS2W[2] / 2);

    //A&#8594;N, T&#8594;N
    var W2N = [];
    W2N[0] = muts[A][T] + muts[A][G] + muts[A][C] + muts[T][A] + muts[T][G] + muts[T][C];
    W2N[2] = qV(muts, A, T) + qV(muts, A, G) + qV(muts, A, C) + qV(muts, T, A) + qV(muts, T, G) + qV(muts, T, C);
    W2N[1] = Math.sqrt(W2N[2] / 6);

    //G&#8594;N, C&#8594;N
    var S2N = [];
    S2N[0] = muts[G][A] + muts[G][T] + muts[G][C] + muts[C][A] + muts[C][G] + muts[C][T];
    S2N[2] = qV(muts, G, A) + qV(muts, G, T) + qV(muts, G, C) + qV(muts, C, A) + qV(muts, C, G) + qV(muts, C, T);
    S2N[1] = Math.sqrt(W2N[2] / 6);
    var types = mutball.types;

    for (var x = 0; x < types.length; x++) {
        var indicator = types[x]; //I hate JS. 'for in' couldn't be used.
        eval("mutball." + indicator + "=rd(" + indicator + "[0])");
        //this[indicator] did not work. So much for dynamic variables.
        eval("mutball." + indicator + "_error=rd(" + indicator + "[1])");
    }
    mutball.source = 'Bias';
    return mutball;
}