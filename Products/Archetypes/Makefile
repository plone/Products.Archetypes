NAME=archetypes
MAJOR_VERSION=1.2
MINOR_VERSION=5
RELEASE_TAG=-rc1
PACKAGE_NAME=${NAME}-${MAJOR_VERSION}.${MINOR_VERSION}${RELEASE_TAG}

PYTHON="/usr/bin/python"
TMPDIR=~/tmp

CURDIR=~/src/archetypes/1_2/Archetypes
BASE_DIR=${CURDIR}/..
SOFTWARE_HOME=~/src/zope/2_7/lib/python
INSTANCE_HOME=~/src/instance/test
PACKAGES=Archetypes validation generator ArchExample ArchGenXML


RM=rm -f
RMRF=rm -rf
FIND=find
XARGS=xargs
CD=cd
LN=ln -sfn
CP=cp
TAR=tar
MKDIR=mkdir -p

.PHONY : clean test reindent reindent_clean sdist
.PHONY : default

# default:     The default step (invoked when make is called without a target)
default: clean test

clean :
	find . \( -name '*~' -o -name '*.py[co]' -o -name '*.bak' \) -exec rm {} \; -print

reindent :
	~/src/reindent.py -r -v .

test :
	export INSTANCE_HOME=${INSTANCE_HOME}; export SOFTWARE_HOME=${SOFTWARE_HOME}; \
	cd ${CURDIR}/tests && ${PYTHON} runalltests.py


# sdist:       Create a source distribution file (implies clean).
#
sdist: reindent clean sdist_tgz

# sdist_tgz:   Create a tgz archive file as a source distribution.
#
sdist_tgz:
	echo -n "${MAJOR_VERSION}.${MINOR_VERSION}${RELEASE_TAG}" >\
          ${CURDIR}/version.txt
	${MKDIR} ${TMPDIR}/${PACKAGE_NAME}
	${CD} ${TMPDIR}/${PACKAGE_NAME} && \
          for package in ${PACKAGES}; do ${LN} ${BASE_DIR}/$$package .; done && \
          ${CD} ${TMPDIR} && ${TAR} czfh ${BASE_DIR}/${PACKAGE_NAME}.tgz ${PACKAGE_NAME} \
           --exclude=${PACKAGE_NAME}.tgz\
           --exclude=CVS \
           --exclude=.cvsignore \
           --exclude=makefile \
           --exclude=Makefile \
           --exclude=*.pyc \
           --exclude=TAGS \
           --exclude=*~ \
           --exclude=.#*
	${RMRF} ${TMPDIR}/${PACKAGE_NAME}
