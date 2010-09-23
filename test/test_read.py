import re
import glob
from nose.tools import *

import asciitable

if asciitable.has_numpy:
    numpy_cases = (True, False)
else:
    numpy_cases = (False,)

def has_numpy_and_not_has_numpy(func):
    """Perform tests that should work for has_numpy==True and has_numpy==False"""
    def wrap():
        for numpy_case in numpy_cases:
            func(numpy=numpy_case)
    wrap.__name__ = func.__name__
    return wrap

def has_numpy(func):
    """Tests that will only succeed if has_numpy == True"""
    def wrap():
        for numpy_case in numpy_cases:
            if numpy_case is True:
                func(numpy=numpy_case)
    wrap.__name__ = func.__name__
    return wrap

@has_numpy_and_not_has_numpy
def test_read_all_files(numpy):
    for testfile in get_testfiles():
        print('Reading %s' % testfile['name'])
        if testfile.get('requires_numpy') and not asciitable.has_numpy:
            return
        table = asciitable.read(testfile['name'], numpy=numpy, **testfile['opts'])
        assert_equal(table.dtype.names, testfile['cols'])
        for colname in table.dtype.names:
            assert_equal(len(table[colname]), testfile['nrows'])

@has_numpy
def test_daophot_header_keywords(numpy):
    reader = asciitable.get_reader(Reader=asciitable.DaophotReader, numpy=numpy)
    table = reader.read('t/daophot.dat')
    expected_keywords = (('NSTARFILE', 'test.nst.1', 'filename', '%-23s'),
                         ('REJFILE', 'hello world', 'filename', '%-23s'),
                         ('SCALE', '1.',  'units/pix', '%-23.7g'),)

    for name, value, units, format_ in expected_keywords:
        for keyword in reader.keywords:
            if keyword.name == name:
                assert_equal(keyword.value, value)
                assert_equal(keyword.units, units)
                assert_equal(keyword.format, format_)
                break
        else:
            raise ValueError('Keyword not found')


@has_numpy_and_not_has_numpy
@raises(asciitable.InconsistentTableError)
def test_empty_table_no_header(numpy):
    table = asciitable.read('t/no_data_without_header.dat', Reader=asciitable.NoHeader, numpy=numpy)

@has_numpy_and_not_has_numpy
@raises(asciitable.InconsistentTableError)
def test_wrong_quote(numpy):
    table = asciitable.read('t/simple.txt', numpy=numpy)

@has_numpy_and_not_has_numpy
@raises(asciitable.InconsistentTableError)
def test_extra_data_col(numpy):
    table = asciitable.read('t/bad.txt', numpy=numpy)

@has_numpy_and_not_has_numpy
@raises(asciitable.InconsistentTableError)
def test_extra_data_col2(numpy):
    table = asciitable.read('t/simple5.txt', delimiter='|', numpy=numpy)

@has_numpy_and_not_has_numpy
@raises(IOError)
def test_missing_file(numpy):
    table = asciitable.read('does_not_exist', numpy=numpy)

@has_numpy_and_not_has_numpy
def test_set_names(numpy):
    names = ('c1','c2','c3', 'c4', 'c5', 'c6')
    include_names = ('c1', 'c3')
    exclude_names = ('c4', 'c5', 'c6')
    data = asciitable.read('t/simple3.txt', names=names, delimiter='|', numpy=numpy)
    assert_equal(data.dtype.names, names)

@has_numpy_and_not_has_numpy
def test_set_include_names(numpy):
    names = ('c1','c2','c3', 'c4', 'c5', 'c6')
    include_names = ('c1', 'c3')
    data = asciitable.read('t/simple3.txt', names=names, include_names=include_names, delimiter='|', numpy=numpy)
    assert_equal(data.dtype.names, include_names)

@has_numpy_and_not_has_numpy
def test_set_exclude_names(numpy):
    exclude_names = ('Y', 'object')
    data = asciitable.read('t/simple3.txt', exclude_names=exclude_names, delimiter='|', numpy=numpy)
    assert_equal(data.dtype.names, ('obsid', 'redshift', 'X', 'rad'))

@has_numpy_and_not_has_numpy
def test_custom_process_lines(numpy):
    def process_lines(lines):
        bars_at_ends = re.compile(r'^\| | \|$', re.VERBOSE)
        striplines = (x.strip() for x in lines)
        return [bars_at_ends.sub('', x) for x in striplines if len(x) > 0]
    reader = asciitable.get_reader(delimiter='|', numpy=numpy)
    reader.inputter.process_lines = process_lines
    data = reader.read('t/bars_at_ends.txt')
    assert_equal(data.dtype.names, ('obsid', 'redshift', 'X', 'Y', 'object', 'rad'))
    assert_equal(len(data), 3)

@has_numpy_and_not_has_numpy
def test_custom_process_line(numpy):
    def process_line(line):
        line_out = re.sub(r'^\|\s*', '', line.strip())
        return line_out
    reader = asciitable.get_reader(data_start=2, delimiter='|', numpy=numpy)
    reader.header.splitter.process_line = process_line
    reader.data.splitter.process_line = process_line
    data = reader.read('t/nls1_stackinfo.dbout')
    cols = get_testfiles('t/nls1_stackinfo.dbout')['cols']
    assert_equal(data.dtype.names, cols[1:])

@has_numpy_and_not_has_numpy
def test_custom_splitters(numpy):
    reader = asciitable.get_reader(numpy=numpy)
    reader.header.splitter = asciitable.BaseSplitter()
    reader.data.splitter = asciitable.BaseSplitter()
    f = 't/test4.dat'
    data = reader.read(f)
    testfile = get_testfiles(f)
    assert_equal(data.dtype.names, testfile['cols'])
    assert_equal(len(data), testfile['nrows'])
    assert_almost_equal(data.field('zabs1.nh')[2], 0.0839710433091)
    assert_almost_equal(data.field('p1.gamma')[2], 1.25997502704)
    assert_almost_equal(data.field('p1.ampl')[2], 0.000696444029148)
    assert_equal(data.field('statname')[2], 'chi2modvar')
    assert_almost_equal(data.field('statval')[2], 497.56468441)
    
@has_numpy_and_not_has_numpy
def test_start_end(numpy):
    data = asciitable.read('t/test5.dat', header_start=1, data_start=3, data_end=-5, numpy=numpy)
    assert_equal(len(data), 13)
    assert_equal(data.field('statname')[0], 'chi2xspecvar')
    assert_equal(data.field('statname')[-1], 'chi2gehrels')

@has_numpy
def test_set_converters(numpy):
    converters = {'zabs1.nh': [asciitable.convert_numpy('int32'),
                               asciitable.convert_numpy('float32')],
                  'p1.gamma': asciitable.convert_numpy('str')
                  }
    data = asciitable.read('t/test4.dat', converters=converters, numpy=numpy)
    assert_equal(str(data['zabs1.nh'].dtype), 'float32')
    assert_equal(data['p1.gamma'][0], '1.26764544642')
    
@has_numpy_and_not_has_numpy
def test_from_string(numpy):
    f = 't/simple.txt'
    table = open(f).read()
    testfile = get_testfiles(f)
    data = asciitable.read(table, numpy=numpy, **testfile['opts'])
    assert_equal(data.dtype.names, testfile['cols'])
    assert_equal(len(data), testfile['nrows'])
    
@has_numpy_and_not_has_numpy
def test_from_lines(numpy):
    f = 't/simple.txt'
    table = open(f).readlines()
    testfile = get_testfiles(f)
    data = asciitable.read(table, numpy=numpy, **testfile['opts'])
    assert_equal(data.dtype.names, testfile['cols'])
    assert_equal(len(data), testfile['nrows'])
    
@has_numpy_and_not_has_numpy
def test_comment_lines(numpy):
    table = asciitable.get_reader(Reader=asciitable.RdbReader, numpy=numpy)
    data = table.read('t/apostrophe.rdb')
    assert_equal(table.comment_lines, ['# first comment', '  # second comment'])
    
def get_testfiles(name=None):
    """Set up information about the columns, number of rows, and reader params to
    read a bunch of test files and verify columns and number of rows."""

    testfiles = [
        {'cols': ('agasc_id', 'n_noids', 'n_obs'),
         'name': 't/apostrophe.rdb',
         'nrows': 2,
         'opts': {'Reader': asciitable.Rdb}},
        {'cols': ('agasc_id', 'n_noids', 'n_obs'),
         'name': 't/apostrophe.tab',
         'nrows': 3,
         'opts': {'Reader': asciitable.Tab}},
        {'cols': ('Index',
                  'RAh',
                  'RAm',
                  'RAs',
                  'DE-',
                  'DEd',
                  'DEm',
                  'DEs',
                  'Match',
                  'Class',
                  'AK',
                  'Fit'),
         'name': 't/cds.dat',
         'nrows': 1,
         'opts': {'Reader': asciitable.Cds}},
        {'cols': ('a', 'b', 'c'),
         'name': 't/commented_header.dat',
         'nrows': 2,
         'opts': {'Reader': asciitable.CommentedHeader}},
        {'cols': ('col1', 'col2', 'col3', 'col4', 'col5'),
         'name': 't/continuation.dat',
         'nrows': 2,
         'opts': {'Inputter': asciitable.ContinuationLinesInputter,
                  'Reader': asciitable.NoHeader}},
        {'cols': ('ID',
                  'XCENTER',
                  'YCENTER',
                  'MAG',
                  'MERR',
                  'MSKY',
                  'NITER',
                  'SHARPNESS',
                  'CHI',
                  'PIER',
                  'PERROR'),
         'name': 't/daophot.dat',
         'nrows': 2,
         'requires_numpy': True,
         'opts': {'Reader': asciitable.Daophot}},
        {'cols': ('ra', 'dec', 'sai', 'v2', 'sptype'),
         'name': 't/ipac.dat',
         'nrows': 2,
         'opts': {'Reader': asciitable.Ipac}},
        {'cols': ('',
                  'objID',
                  'osrcid',
                  'xsrcid',
                  'SpecObjID',
                  'ra',
                  'dec',
                  'obsid',
                  'ccdid',
                  'z',
                  'modelMag_i',
                  'modelMagErr_i',
                  'modelMag_r',
                  'modelMagErr_r',
                  'expo',
                  'theta',
                  'rad_ecf_39',
                  'detlim90',
                  'fBlim90'),
         'name': 't/nls1_stackinfo.dbout',
         'nrows': 58,
         'opts': {'data_start': 2, 'delimiter': '|'}},
        {'cols': ('Index',
                  'RAh',
                  'RAm',
                  'RAs',
                  'DE-',
                  'DEd',
                  'DEm',
                  'DEs',
                  'Match',
                  'Class',
                  'AK',
                  'Fit'),
         'name': 't/no_data_cds.dat',
         'nrows': 0,
         'opts': {'Reader': asciitable.Cds}},
        {'cols': ('ID',
                  'XCENTER',
                  'YCENTER',
                  'MAG',
                  'MERR',
                  'MSKY',
                  'NITER',
                  'SHARPNESS',
                  'CHI',
                  'PIER',
                  'PERROR'),
         'name': 't/no_data_daophot.dat',
         'nrows': 0,
         'requires_numpy': True,
         'opts': {'Reader': asciitable.Daophot}},
        {'cols': ('ra', 'dec', 'sai', 'v2', 'sptype'),
         'name': 't/no_data_ipac.dat',
         'nrows': 0,
         'opts': {'Reader': asciitable.Ipac}},
        {'cols': ('a', 'b', 'c'),
         'name': 't/no_data_with_header.dat',
         'nrows': 0,
         'opts': {}},
        {'cols': ('agasc_id', 'n_noids', 'n_obs'),
         'name': 't/short.rdb',
         'nrows': 7,
         'opts': {'Reader': asciitable.Rdb}},
        {'cols': ('agasc_id', 'n_noids', 'n_obs'),
         'name': 't/short.tab',
         'nrows': 7,
         'opts': {'Reader': asciitable.Tab}},
        {'cols': ('test 1a', 'test2', 'test3', 'test4'),
         'name': 't/simple.txt',
         'nrows': 2,
         'opts': {'quotechar': "'"}},
        {'cols': ('obsid', 'redshift', 'X', 'Y', 'object', 'rad'),
         'name': 't/simple2.txt',
         'nrows': 3,
         'opts': {'delimiter': '|'}},
        {'cols': ('obsid', 'redshift', 'X', 'Y', 'object', 'rad'),
         'name': 't/simple3.txt',
         'nrows': 2,
         'opts': {'delimiter': '|'}},
        {'cols': ('col1', 'col2', 'col3', 'col4', 'col5', 'col6'),
         'name': 't/simple4.txt',
         'nrows': 3,
         'opts': {'Reader': asciitable.NoHeader, 'delimiter': '|'}},
        {'cols': ('obsid', 'offset', 'x', 'y', 'name', 'oaa'),
         'name': 't/space_delim_blank_lines.txt',
         'nrows': 3,
         'opts': {}},
        {'cols': ('zabs1.nh', 'p1.gamma', 'p1.ampl', 'statname', 'statval'),
         'name': 't/test4.dat',
         'nrows': 1172,
         'opts': {}}]

    if name is not None:
        return [x for x in testfiles if x['name'] == name][0]
    else:
        return testfiles
    