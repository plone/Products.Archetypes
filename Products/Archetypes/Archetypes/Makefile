NAME=archetypes
MAJOR_VERSION=1.3
MINOR_VERSION=0
RELEASE_TAG=_b2
PACKAGE_NAME=${NAME}-${MAJOR_VERSION}.${MINOR_VERSION}${RELEASE_TAG}
CVSTAG=release-1_3_0-b2

PYTHON="/usr/bin/python"
TMPDIR=~/tmp

CURDIR=~/src/archetypes/1_3/Archetypes
BASE_DIR=${CURDIR}/..
SOFTWARE_HOME=~/src/zope/2_7/lib/python
INSTANCE_HOME=~/src/instance/shellex
PACKAGES=Archetypes validation generator ArchExample ArchGenXML
CVSROOT=-d:ext:dreamcatcher@cvs.sf.net:/cvsroot/archetypes

RM=rm -f
RMRF=rm -rf
FIND=find
XARGS=xargs
CD=cd
LN=ln -sfn
CP=cp
TAR=tar
MKDIR=mkdir -p
CVS=cvs

.PHONY : clean test reindent reindent_clean sdist
.PHONY : default

# default:     The default step (invoked when make is called without a target)
default: clean test

tag :
	for package in ${PACKAGES}; do ${CD} ${BASE_DIR}/$$package && ${CVS} tag -F -R ${CVSTAG}; done

clean_checkin :
	for package in ${PACKAGES}; do ${CD} ${BASE_DIR}/$$package && ${CVS} ci -m"Cleanup whitespace"; done

clean :
	find . \( -name '*~' -o -name '*.py[co]' -o -name '*.bak' \) -exec rm {} \; -print

reindent :
	~/src/reindent.py -r -v .

test :
	export INSTANCE_HOME=${INSTANCE_HOME}; export SOFTWARE_HOME=${SOFTWARE_HOME}; \
	cd ${CURDIR}/tests && ${PYTHON} runalltests.py


bump_version :
	echo -n "${MAJOR_VERSION}.${MINOR_VERSION}${RELEASE_TAG}" >\
          ${CURDIR}/version.txt

cleanup : bump_version reindent clean clean_checkin

cleanup_tag : cleanup tag

export :
	${RMRF} ${TMPDIR}/${PACKAGE_NAME}
	${MKDIR} ${TMPDIR}/${PACKAGE_NAME}
	${CD} ${TMPDIR}/${PACKAGE_NAME} && \
          for package in ${PACKAGES}; do cvs ${CVSROOT} export -kv -r ${CVSTAG} $$package; done

# sdist:       Create a source distribution file (implies clean).
#
sdist: cleanup_tag export sdist_tgz


# sdist_tgz:   Create a tgz archive file as a source distribution.
#
sdist_tgz:
	${CD} ${TMPDIR} && ${TAR} czfh ${BASE_DIR}/${PACKAGE_NAME}.tgz ${PACKAGE_NAME} \
           --exclude=${PACKAGE_NAME}.tgz\
           --exclude=CVS \
           --exclude=.cvsignore \
           --exclude=makefile \
           --exclude=Makefile \
           --exclude=debian \
           --exclude=*.pyc \
           --exclude=TAGS \
           --exclude=*~ \
           --exclude=.#*
	${RMRF} ${TMPDIR}/${PACKAGE_NAME}
