 
#Makefile

BUILDDIR=./BUILD
DOCSDIR=./DOCS


SOURCE = *.py render/*.py

PYDOC_APP=epydoc

PYTHON=${SOFTWARE}/wrappers/python

PYTHONPATH:=..:${PYTHONPATH}

PYGRID_BUILD:=$(BUILDDIR)

all: docs tests

$(BUILDDIR):
	mkdir -p $@

$(DOCSDIR):
	mkdir -p $@

TESTS = tests/test_3delight.py \
		tests/test_command.py \
		tests/test_houdini.py \
		tests/test_mantra.py \
		tests/test_maya_batch.py \
		tests/test_maya_mr.py \
		tests/test_maya_sw.py \
		tests/test_mkdaily.py \
		tests/test_nuke.py \

tests: $(BUILDDIR) $(TESTS)
	$(foreach test,$(TESTS),echo;\
	echo TEST :: $(test);\
	export PYGRID_BUILD=${PYGRID_BUILD};\
	echo ${PYGRID_BUILD};\
	$(PYTHON) $(test);)

docs: $(DOCSDIR)
	$(PYDOC_APP) -o $(DOCSDIR) ${PWD};

clean:
	rm -fv *.pyc */*.pyc
	