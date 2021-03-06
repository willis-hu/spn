import os
import time
import pickle

import numpy as np

from spn.spn import *
from util.util import *
from .experiment import Experiment

DATADIR = 'data'
OUTDIR = 'results'

def make_kfold_filenames(vartype, name, k):
	filenames = [os.path.join(DATADIR, vartype, name, "{0}.{1}.data".format(name, i+1))
	             for i in range(k)]
	return filenames

def make_train_test_filenames(vartype, name):
	trainfiles = [os.path.join(DATADIR, vartype, name, "{0}.train.data".format(name))]
	testfiles = [os.path.join(DATADIR, vartype, name, "{0}.test.data".format(name))]
	return trainfiles, testfiles

def run_train_test(trainfiles, testfiles, numvar, numcomp, params):
	model = SPN(numvar, numcomp, params)
	experiment = Experiment(model, trainfiles, testfiles)
	t0 = time.clock()
	result = experiment.run()
	t1 = time.clock()
	return result, t1-t0, model

def run_ith_fold(i, filenames, numvar, numcomp, params):
	testfiles = filenames[i:i+1]
	trainfiles = filenames[i+1:] + filenames[:i]
	return run_train_test(trainfiles, testfiles, numvar, numcomp, params)

def run_kfold(vartype, name, k, numvar, numcomp, params):
	filenames = make_kfold_filenames(vartype, name, k)
	results = [None] * k
	times = [None] * k
	models = [None] * k
	numnodes = [None] * k
	numparams = [None] * k
	for i in range(k):
		results[i], times[i], models[i] = run_ith_fold(i, filenames, numvar, numcomp, params)
		numnodes[i] = count_nodes(models[i])
		numparams[i] = count_params(models[i])
		print(i, results[i], times[i], numnodes[i], numparams[i])
	print(np.mean(results), np.std(results))
	return results, times, models, numnodes, numparams

def run(vartype, traintest, name, numvar, numcomp, batchsize, mergebatch, corrthresh,
        equalweight, updatestruct, mvmaxscope, leaftype):
	outfile = "{0}_{1}_{2}_{3}_{4}_{5}".format(name, numcomp, batchsize, mergebatch,
                           corrthresh, mvmaxscope)

	if not os.path.exists(OUTDIR):
		os.makedirs(OUTDIR)

	resultpath = os.path.join(OUTDIR, "{0}.txt".format(outfile))
	picklepath = os.path.join(OUTDIR, "{0}.pkl".format(outfile))
	params = SPNParams(batchsize, mergebatch, corrthresh, equalweight, updatestruct,
	    mvmaxscope, leaftype)

	print('******{0}*******'.format(name))

	if traintest:
		trainfiles, testfiles = make_train_test_filenames(vartype, name)
		result, t, model = run_train_test(trainfiles, testfiles, numvar, numcomp, params)
		numnodes = count_nodes(model)
		numparams = count_params(model)
		print('Loglhd: {0:.3f}'.format(result))
		print('Time: {0:.3f}'.format(t))
		print('Number of nodes: {0}'.format(numnodes))
		print('Number of parameters: {0}'.format(numparams))
		with open(resultpath, 'w') as g:
			g.write('Loglhd: {0:.3f}\n'.format(result))
			g.write('Time: {0:.3f}\n'.format(t))
			g.write('Number of nodes: {0}\n'.format(numnodes))
			g.write('Number of parameters: {0}\n'.format(numparams))
			g.close()
		with open(picklepath, 'wb') as g:
			pickle.dump(model, g)
	else:
		results, times, models, numnodes, numparams = run_kfold(
		                    vartype, name, 10, numvar, numcomp, params)

		with open(resultpath, 'w') as g:
			g.write('Loglhd: {0:.3f}, {1:.3f}\n'.format(np.mean(results), np.std(results)))
			g.write('Times: {0:.3f}, {1:.3f}\n'.format(np.mean(times), np.std(times)))
			g.write('NumNodes: {0:.1f}, {1:.3f}\n'.format(np.mean(numnodes), np.std(numnodes)))
			g.write('NumParams: {0:.3f}, {1:.3f}\n'.format(np.mean(numparams), np.std(numparams)))
			g.write('\n')
			for r, t, a, b in zip(results, times, numnodes, numparams):
				g.write('{0:.3f} {1:.3f} {2} {3}\n'.format(r, t, a, b))
			g.close()
		with open(picklepath, 'wb') as g:
			pickle.dump(models, g)


