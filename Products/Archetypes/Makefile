NAME=Archetypes
MAJOR_VERSION=1.3
MINOR_VERSION=1
RELEASE_TAG=-rc11
PACKAGE_NAME=${NAME}-${MAJOR_VERSION}.${MINOR_VERSION}${RELEASE_TAG}
TAG=${PACKAGE_NAME}

PYTHON="/usr/bin/python"
TMPDIR=~/tmp

CURDIR=~/dev/zope2/archetypes/Archetypes/branches/release-1_3-branch
BASE_DIR=${CURDIR}/..
SOFTWARE_HOME=/usr/lib/zope/Zope-2_7-branch
INSTANCE_HOME=/var/lib/zope/plone
ZOPE_CONFIG=${INSTANCE_HOME}/etc/zope.conf.test
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
	export INSTANCE_HOME=${INSTANCE_HOME}; \
	export SOFTWARE_HOME=${SOFTWARE_HOME}; \
	export ZOPE_CONFIG=${ZOPE_CONFIG}; \
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
