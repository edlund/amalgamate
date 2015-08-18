#!/bin/bash

# amalgamate.py - Amalgamate C source and header files.
# Copyright (c) 2012, Erik Edlund <erik.edlund@32767.se>
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
#  * Redistributions of source code must retain the above copyright notice,
#  this list of conditions and the following disclaimer.
# 
#  * Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
# 
#  * Neither the name of Erik Edlund, nor the names of its contributors may
#  be used to endorse or promote products derived from this software without
#  specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

SCRIPTPATH=`readlink -f $0`
SCRIPTDIR="`dirname ${SCRIPTPATH}`"
TESTDIR="${SCRIPTDIR}/test"

function test_amalgamation {
	FILE=$1
	CONFIG_FILE="${TESTDIR}/${FILE}.json"
	PROLOGUE_FILE="${TESTDIR}/${FILE}.prologue"
	EXPECTED_FILE="${TESTDIR}/${FILE}.expected"
	GENERATED_FILE="${FILE}"
	
	echo "test_amalgamation \"${FILE}\"..."
	"${SCRIPTDIR}/amalgamate.py" \
		"--config=${CONFIG_FILE}" \
		"--source=${TESTDIR}" \
		"--prologue=${PROLOGUE_FILE}" \
		"--verbose=yes"
	
	DIFF=`diff -Nur ${EXPECTED_FILE} ${GENERATED_FILE}`
	if [ "${DIFF}" ]; then
		echo "*** TEST FAILURE ***" 1>&2
		echo "Unexpected diff:" 1>&2
		echo "${DIFF}" 1>&2
		exit 1
	fi
	echo "...pass!"
	echo ""
}

test_amalgamation "source.c"
test_amalgamation "include.h"

function test_command {
	CMD=$1
	MSG=$2
	
	echo "test_command \"${CMD}\"..."
	`${CMD}`
	EXIT=$?
	if [ ! $EXIT -eq 0 ]; then
		echo "*** TEST FAILURE ***" 1>&2
		echo "Exit status: ${EXIT}" 1>&2
		exit 1
	fi
}

test_command "cc -Wall -Wextra -o source.out source.c"
test_command "./source.out"
test_command "rm -f include.h source.c source.out"

