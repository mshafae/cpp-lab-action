#!/usr/bin/env python3
#
# Copyright 2021-2023 Michael Shafae
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
""" Check student's submission; requires the main file and the
    template file from the original repository. """
# pexpect documentation
#  https://pexpect.readthedocs.io/en/stable/index.html

# ex.
# .action/solution_check_p1.py  part-1 asgt

import io
import math
import sys
import os
import re
import pexpect
from assessment import csv_solution_check_make
from logger import setup_logger

import lab_config as cfg


def regex_it(s):
    combine_white_space_regex = re.compile(r"\s+")
    s = combine_white_space_regex.sub(" ", s).strip()
    s = s.replace(' ', '\\s+').replace('\n', '\\s+')
    return f'\\s*{s}\\s*'


def run_p1(binary):
    """Run part-1 Olympic Judge Average"""
    logger = setup_logger()
    status = []
    error_values = (
        [None, 'error: you must give at least three scores'],  # 0 args, too few
        ['1', 'error: you must give at least three scores'],  # 1 arg, too few
        [
            '1',
            '2',
            'error: you must give at least three scores',
        ],  # 2 args, too few
    )
    values = (
        [5, 5, 5, 5],  # all same
        [0, 0, 0, 0],  # zeroes
        [1, 2, 3, 2],  # 3 increasing
        [3, 2, 1, 2],  # 3 decreasing
        [5.1, 8.7, 9.0, 2.6, 1.9, 5.46667],  # 5 floats
        # all 24 permutations of 3 5 7 8
        [3, 5, 7, 8, 6],
        [3, 5, 8, 7, 6],
        [3, 7, 5, 8, 6],
        [3, 7, 8, 5, 6],
        [3, 8, 5, 7, 6],
        [3, 8, 7, 5, 6],
        [5, 3, 7, 8, 6],
        [5, 3, 8, 7, 6],
        [5, 7, 3, 8, 6],
        [5, 7, 8, 3, 6],
        [5, 8, 3, 7, 6],
        [5, 8, 7, 3, 6],
        [7, 3, 5, 8, 6],
        [7, 3, 8, 5, 6],
        [7, 5, 3, 8, 6],
        [7, 5, 8, 3, 6],
        [7, 8, 3, 5, 6],
        [7, 8, 5, 3, 6],
        [8, 3, 5, 7, 6],
        [8, 3, 7, 5, 6],
        [8, 5, 3, 7, 6],
        [8, 5, 7, 3, 6],
        [8, 7, 3, 5, 6],
        [8, 7, 5, 3, 6],
        # minimum is duplicated, but should only be omitted once
        [3, 1, 1, 5, 2],
        # maximum is duplicated, but should only be omitted once
        [4, 2, 9, 9, 3, 5.33333],
    )
    for index, val in enumerate(error_values):
        test_number = index + 1
        logger.info('Test %d - %s', test_number, val)
        rv = _run_p1_error(binary, val)
        if not rv:
            logger.error(
                "Did not receive expected response for test %d.", test_number
            )
        status.append(rv)

    for index, val in enumerate(values):
        test_number = len(error_values) + index + 1
        logger.info('Test %d - %s', test_number, val)
        rv = _run_p1(binary, val)
        if not rv:
            logger.error(
                "Did not receive expected response for test %d.", test_number
            )
        status.append(rv)
    return status


def _run_p1_error(binary, values):
    logger = setup_logger()
    status = False
    if values[0] is None:
        proc = pexpect.spawn(binary, timeout=1)
    else:
        argument_strings = list(map(str, values[:-1]))
        proc = pexpect.spawn(binary, timeout=1, args=argument_strings)

    expected = values[-1]

    with io.BytesIO() as log_stream:
        proc.logfile = log_stream
        try:
            regex = expected.replace(' ', '\\s+')
            proc.expect(fr'(?i).*{regex}.*')
        except (
            pexpect.exceptions.TIMEOUT,
            pexpect.exceptions.EOF,
        ) as exception:
            logger.error(f'Expected: "{expected}"')
            logger.error('Could not find expected output.')
            logger.error(
                'Your output: "%s"', log_stream.getvalue().decode('utf-8')
            )
            logger.debug("%s", str(exception))
            logger.debug(str(proc))
            return status

        proc.expect(pexpect.EOF)
        proc.close()
        if proc.exitstatus == 0:
            logger.error("Expected: non-zero exit code.")
            logger.error(f'Exit code was {proc.exitstatus}.')
            logger.error("Program returned zero, but non-zero is required")
            logger.error(
                'Your output: "%s"', log_stream.getvalue().decode('utf-8')
            )
            return status
    status = True
    return status


def _run_p1(binary, values):
    """The actual test with the expected input and output"""
    logger = setup_logger()
    status = False
    argument_strings = list(map(str, values[:-1]))
    expected_float = values[-1]
    proc = pexpect.spawn(binary, timeout=1, args=argument_strings)
    # proc.logfile = sys.stdout.buffer

    with io.BytesIO() as log_stream:
        proc.logfile = log_stream
        try:
            match_index = proc.expect(
                r'(?i)\s*average\s*is\s*([-+]?[0-9]+[.]?[0-9]*([eE][-+]?[0-9]+)?)\s*'
            )

            token = proc.match.group(1).decode("utf-8")
            actual = float(token)
            # 1% tolerance
            if not math.isclose(expected_float, actual, rel_tol=0.01):
                logger.error(
                    'actual numeric output is %f, which does not equal %f',
                    actual,
                    expected_float,
                )
                return status

        except (
            pexpect.exceptions.TIMEOUT,
            pexpect.exceptions.EOF,
        ) as exception:
            logger.error('Expected: "average is ' + str(expected_float) + '"')
            logger.error('Could not find expected output.')
            logger.error(
                'Your output: "%s"', log_stream.getvalue().decode('utf-8')
            )
            logger.debug("%s", str(exception))
            logger.debug(str(proc))
            return status

        proc.expect(pexpect.EOF)
        proc.close()
        if proc.exitstatus != 0:
            logger.error("Expected: zero exit code.")
            logger.error(f'Exit code was {proc.exitstatus}.')
            logger.error("Program returned non-zero, but zero is required")
            logger.error(
                'Your output: "%s"', log_stream.getvalue().decode('utf-8')
            )
            return status

    status = True
    return status


def run_p2(binary):
    """Run part-2 Dining 2-Philosophers Schedule"""
    logger = setup_logger()
    status = []
    # MS: You can't check for errors because the input is interactive.
    # The computer user must enter something to move the program forward.
    # The concept of arguments do not exist.
    # Checking for input that does not use the "s" or "e" tokens is not
    # defined in the assignment's requirements.
    error_values = (
        # [],  # 0 arguments, too few
        # ['sss'],  # 1 arguments, too few
        # ['sss', 'sss', 'eee'],  # 3 arguments, too many
        # ['sss', 'eee', 'sss', 'eee'],  # 4 arguments, too many
    )
    values = (
        ['sss', 'sss', 'Valid schedule'],  # all sleep, OK
        ['ses', 'ese', 'Valid schedule'],  # alternate sleep-eat, OK
        ['ese', 'ses', 'Valid schedule'],  # alternate eat-sleep, OK
        ['eee', 'sss', 'Valid schedule'],  # first eats, second sleeps, OK
        ['eee', 'eee', 'Invalid schedule'],  # all eat, Not OK
        ['sse', 'sse', 'Invalid schedule'],  # each eats at time 2, not OK
        ['ses', 'ses', 'Invalid schedule'],  # each eats at time 1, not OK
        ['ess', 'ess', 'Invalid schedule'],  # each eats at time 0, not OK
    )

    for index, val in enumerate(error_values):
        test_number = index + 1
        logger.info('Test %d - %s', test_number, val)
        rv = _run_p2_error(binary, val)
        if not rv:
            logger.error(
                "Did not receive expected response for test %d.", test_number
            )
        status.append(rv)

    for index, val in enumerate(values):
        test_number = len(error_values) + index + 1
        logger.info('Test %d - %s', test_number, val)
        rv = _run_p2(binary, val)
        if not rv:
            logger.error(
                "Did not receive expected response for test %d.", test_number
            )
        status.append(rv)
    return status


def _run_p2_error(binary, values):
    print('p2 error not implemented')
    return True


# Copied from Lab 3 - part 1, Fall 2023 and adapted
def _run_p2(binary, values):
    """The actual test with the expected input and output"""
    logger = setup_logger()
    status = False
    proc = pexpect.spawn(binary, timeout=1)
    # proc.logfile = sys.stdout.buffer

    expected = values[-1]
    values = list(map(str, values))

    prompts = [
        'Please enter the schedule of Philosopher 1: ',
        'Please enter the schedule of Philosopher 2: ',
    ]

    for curr_prompt, response in zip(prompts, values):
        regex_prompt = regex_it(curr_prompt)
        try:
            proc.expect(
                fr'(?i){regex_prompt}'
            )
        except (pexpect.exceptions.TIMEOUT, pexpect.exceptions.EOF) as exception:
            expected_error = f'Expected: "{curr_prompt}"'
            logger.error(expected_error)
            logger.error('Could not find expected output.')
            logger.info("%s", str(exception))
            logger.debug(str(proc))
            return status

        proc.sendline(response)

    regex_expected = regex_it(expected)
    try:
        proc.expect(
            fr'(?i){regex_expected}'
        )
    except (pexpect.exceptions.TIMEOUT, pexpect.exceptions.EOF) as exception:
        expected_error = f'Expected: "{expected}"'
        logger.error(expected_error)
        logger.error('Could not find expected output.')
        logger.info("%s", str(exception))
        logger.debug(str(proc))
        return status

    proc.expect(pexpect.EOF)
    proc.close()
    if proc.exitstatus == 0:
        status = True
    return status




tidy_opts = (
    '-checks="*,-misc-unused-parameters,'
    '-modernize-use-trailing-return-type,-google-build-using-namespace,'
    '-cppcoreguidelines-avoid-magic-numbers,-readability-magic-numbers,'
    '-fuchsia-default-arguments-calls,-clang-analyzer-deadcode.DeadStores,'
    '-modernize-use-nodiscard,-modernize-pass-by-value,'
    '-bugprone-exception-escape,-llvm-header-guard"'
    ' -config="{CheckOptions: [{key: readability-identifier-naming.ClassCase, value: CamelCase}, '
    '{key: readability-identifier-naming.ClassMemberCase, value: lower_case}, '
    '{key: readability-identifier-naming.ConstexprVariableCase, value: CamelCase}, '
    '{key: readability-identifier-naming.ConstexprVariablePrefix, value: k}, '
    '{key: readability-identifier-naming.EnumCase, value: CamelCase}, '
    '{key: readability-identifier-naming.EnumConstantCase, value: CamelCase}, '
    '{key: readability-identifier-naming.EnumConstantPrefix, value: k}, '
    '{key: readability-identifier-naming.FunctionCase, value: CamelCase}, '
    '{key: readability-identifier-naming.GlobalConstantCase, value: CamelCase}, '
    '{key: readability-identifier-naming.GlobalConstantPrefix, value: k}, '
    '{key: readability-identifier-naming.StaticConstantCase, value: CamelCase}, '
    '{key: readability-identifier-naming.StaticConstantPrefix, value: k}, '
    '{key: readability-identifier-naming.StaticVariableCase, value: lower_case}, '
    '{key: readability-identifier-naming.MacroDefinitionCase, value: UPPER_CASE}, '
    '{key: readability-identifier-naming.MacroDefinitionIgnoredRegexp, value: \'^[A-Z]+(_[A-Z]+)*_$\'}, '
    '{key: readability-identifier-naming.MemberCase, value: lower_case}, '
    '{key: readability-identifier-naming.PrivateMemberSuffix, value: _}, '
    '{key: readability-identifier-naming.PublicMemberSuffix, value: \'\'}, '
    '{key: readability-identifier-naming.NamespaceCase, value: lower_case}, '
    '{key: readability-identifier-naming.ParameterCase, value: lower_case}, '
    '{key: readability-identifier-naming.TypeAliasCase, value: CamelCase}, '
    '{key: readability-identifier-naming.TypedefCase, value: CamelCase}, '
    '{key: readability-identifier-naming.VariableCase, value: lower_case}, '
    '{key: readability-identifier-naming.IgnoreMainLikeFunctions, value: 1}]}"'
)

if __name__ == '__main__':
    cwd = os.getcwd()
    repo_name = os.path.basename(cwd)
    td = sys.argv[1]
    # print(td)
    if sys.argv[1] == 'part-1':
        part_config = cfg.lab['parts'][0]
    elif sys.argv[1] == 'part-2':
        part_config = cfg.lab['parts'][1]
    else:
        print(f'Error: {sys.argv[0]} no match.')
        sys.exit(1)

    _program_name = part_config['target']
    _files = part_config['src'].split() + part_config['header'].split()
    _do_format_check = part_config['do_format_check']
    _do_lint_check = part_config['do_lint_check']
    _do_unit_tests = part_config['do_unit_tests']
    _tidy_options = part_config['tidy_opts']
    _skip_compile_cmd = part_config['skip_compile_cmd']
    # There needs to be some magic here to figure out which due date to use.
    _lab_due_date = cfg.lab['mon_duedate'].isoformat()
    _run_func = locals()[part_config['test_main']]

    # Execute the solution check
    csv_solution_check_make(
        csv_key=repo_name,
        target_directory=td,
        program_name=_program_name,
        run=_run_func,
        files=_files,
        do_format_check=_do_format_check,
        do_lint_check=_do_lint_check,
        do_unit_tests=_do_unit_tests,
        tidy_options=_tidy_options,
        skip_compile_cmd=_skip_compile_cmd,
        lab_due_date=_lab_due_date,
    )
