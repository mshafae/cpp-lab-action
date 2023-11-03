#
# Copyright 2021-2022 Michael Shafae
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
""" Utilities to build, run, and evaluate student projects. """
import csv
import json
import os
import pathlib
import pickle
import re
import sys
import subprocess
from datetime import date
from datetime import datetime
from checks import header_check
from ccsrcutilities import (
    glob_all_src_files,
    strip_and_compare_files,
    format_check,
    lint_check,
    glob_cc_src_files,
)
from parse_header import dict_header, null_dict_header
from logger import setup_logger
import lab_config as cfg


def days_late(due_date_isoformat, last_commit_isoformat):
    """Calculate the number of days late given to ISO 8601 datetime strings"""
    due_date = datetime.fromisoformat(due_date_isoformat)
    last_commit = datetime.fromisoformat(last_commit_isoformat)
    late = last_commit - due_date
    return late.days


def last_commit_to_main_reflog(repository_path):
    """Using git, find the last commit in the main branch and return the date."""
    logger = setup_logger()
    cmd = f'git -C "{repository_path}" log -1 --format=%cs'
    logger.debug(cmd)
    status = True
    proc = subprocess.run(
        [cmd],
        capture_output=True,
        shell=True,
        timeout=15,
        check=False,
        text=True,
    )
    last_commit_date = '1969-01-01'
    if proc.stdout:
        last_commit_date = str(proc.stdout).rstrip("\n\r")
    else:
        logger.warning(
            'Not a Git repository, cannot determine last commit date to main in reflog.'
        )
    if proc.stderr:
        logger.debug('stderr: %s', str(proc.stderr).rstrip("\n\r"))
    if proc.returncode != 0:
        status = False
    return (status, last_commit_date)


def seconds_since_epoch_to_isoformat(seconds):
    """Convert seconds into an ISO format date string"""
    a_date = date.fromtimestamp(seconds)
    return a_date.isoformat()


def make_spotless(target_dir):
    """Given a directory that contains a GNU Makefile, clean with the `make
    spotless` target."""
    status = True
    status = make(target_dir, 'spotless')
    return status


def make_build(target_dir, always_clean=True):
    """Given a directory that contains a GNU Makefile, build with `make all`.
    This function call will call `make spotless` via make_spotless()"""
    status = True
    if always_clean:
        status = make_spotless(target_dir)
    if status:
        status = make(target_dir, 'all')
    return status


def make_unittest(
    target_dir,
    always_clean=True,
    output_format="json",
    output_file="test_detail.json",
):
    """Given a directory that contains a GNU Makefile, build with `make unittest`.
    This function call will call `make spotless` via make_spotless()"""
    status = True
    os.environ['GTEST_OUTPUT_FORMAT'] = output_format
    os.environ['GTEST_OUTPUT_FILE'] = output_file
    if always_clean:
        status = make_spotless(target_dir)
    if status:
        status = make(target_dir, 'unittest', time_out=120)
    del os.environ['GTEST_OUTPUT_FORMAT']
    del os.environ['GTEST_OUTPUT_FILE']
    return status


def make(target_dir, make_target, time_out=30):
    """Given a directory, execute make_target given the GNU Makefile in the
    directory."""
    status = True
    logger = setup_logger()
    makefile_name = cfg.lab['makefile_name']
    if cfg.lab['hidden_makefiles']:
        makefile_name = '.' + makefile_name
    if not os.path.exists(os.path.join(target_dir, makefile_name)):
        logger.error(
            'Makefile "%s" does not exist in %s', makefile_name, target_dir
        )
        status = False
    else:
        cmd = f'make -f {makefile_name} -C {target_dir} {make_target}'
        logger.debug(cmd)
        proc = subprocess.run(
            [cmd],
            capture_output=True,
            shell=True,
            timeout=time_out,
            check=False,
            text=True,
        )
        # if proc.stdout:
        #    logger.info('stdout: %s', str(proc.stdout).rstrip("\n\r"))
        if proc.stderr:
            logger.info('stderr: %s', str(proc.stderr).rstrip("\n\r"))
        if proc.returncode != 0:
            status = False
    return status


def build(
    file,
    target='asgt',
    compiletimeout=10,
    compile_cmd='clang++ -Wall -pedantic -std=c++17 -o {0} {1}',
):
    """Given a C++ source file, build with clang C++17 with -Wall
    and -pedantic. Output is 'asgt'. Binary is left on the file system."""
    logger = setup_logger()
    # rm the file if exists
    if os.path.exists(target):
        os.unlink(target)
    status = True
    cmd = compile_cmd.format(target, file)
    logger.debug(cmd)
    proc = subprocess.run(
        [cmd],
        capture_output=True,
        shell=True,
        timeout=compiletimeout,
        check=False,
        text=True,
    )
    if proc.stdout:
        logger.info('stdout: %s', str(proc.stdout).rstrip("\n\r"))
    if proc.stderr:
        logger.info('stderr: %s', str(proc.stderr).rstrip("\n\r"))
    if proc.returncode != 0:
        status = False
    return status


def identify(header):
    """String to identify submission's owner."""
    ident = '(Malformed Header)'
    if header:
        ident = f"Testing {header['name']} {header['email']} {header['github']}"
    return ident


def has_main_function(file):
    """Check if a given file has a C++ main function."""
    status = False
    main_regex = re.compile(
        r'int\s*main\s*\(\s*(?:int\s*argc,\s*(const)?\s*char\s*(const)?\s*\*\s*argv\[\]|void|)\s*\)'
    )
    with open(file, 'r', encoding='UTF-8') as file_handle:
        src_code = file_handle.read()
        matches = main_regex.search(src_code)
        if matches:
            status = True
    return status


# pylint: disable-next=too-many-branches,too-many-statements,too-many-locals,too-many-arguments
def csv_solution_check_make(
    csv_key,
    target_directory,
    program_name='asgt',
    base_directory=None,
    run=None,
    files=None,
    do_format_check=True,
    do_lint_check=True,
    do_unit_tests=True,
    tidy_options=None,
    skip_compile_cmd=False,
    lab_due_date=None,
):
    """Main function for checking student's solution. Provide a pointer to a
    run function."""
    logger = setup_logger()

    students_dict = None

    # XXX
    # More problems here
    # The workflows create a directory named after the repository
    # and then clone the repository into that directory. The CWD
    # is the repository root and not the part. When run from
    # Make, the CWD is the part and not the repository root.
    # print(f'target_directory {target_directory}')
    # print(f'CWD: {os.getcwd()}')
    if os.path.basename(os.getcwd()) != target_directory:
        # This is a GitHub action running the solution check
        # directly as a standalone progrom. The program will be
        # running outside of the part directory.
        # print('case 1')
        abs_path_target_dir = os.path.join(os.getcwd(), target_directory)
        repo_root = os.getcwd()
        cwd_name = os.path.basename(os.getcwd())
        repo_name = os.path.basename(repo_root)
        part_name = target_directory

    else:
        # This is a shell started by Make which will have the CWD
        # the same as the part being tested
        # print('case 2')
        # abs_path_target_dir = os.path.abspath(target_directory)
        abs_path_target_dir = os.getcwd()
        # repo_root = os.path.dirname(abs_path_target_dir)
        repo_root = os.path.normpath(os.path.join(os.getcwd(), '..'))
        # cwd_name = os.path.basename(abs_path_target_dir)
        cwd_name = os.path.basename(os.getcwd())
        # repo_name = csv_key
        repo_name = os.path.basename(repo_root)
        part_name = cwd_name

    csv_filename = f'.{repo_name}_{part_name}_gradelog.csv'
    # print(f'abs_path_target_dir: {abs_path_target_dir}')
    # print(f'repo_root: {repo_root}')
    # print(f'cwd_name: {cwd_name}')
    csv_path = os.path.join(repo_root, csv_filename)
    # print(f'csv_path: {csv_path}')
    # End more problems here.
    csv_fields = [
        'Repo Name',
        'Part',
        'Author',
        'Partner1',
        'Partner2',
        'Partner3',
        'PartnerN',
        'Header',
        'Formatting',
        'Linting',
        'Build',
        'Tests',
        'UnitTests',
        'Notes',
        'UnitTestNotes',
        'DaysLate',
    ]
    status = 0
    with open(csv_path, 'w', encoding='UTF-8') as csv_output_handle:
        outcsv = csv.DictWriter(csv_output_handle, csv_fields)
        outcsv.writeheader()
        row = {}
        row['Repo Name'] = repo_name
        row['Part'] = part_name
        if not lab_due_date:
            # set a default date that is safe
            lab_due_date = date.today().isoformat()
        valid_date, last_commit = last_commit_to_main_reflog(
            abs_path_target_dir
        )
        if not valid_date:
            last_commit = date.today().isoformat()
        row['DaysLate'] = days_late(lab_due_date, last_commit)
        # Init to empty string so you're always adding notes.
        row['Notes'] = ''
        if not files:
            # This could be a target in the Makefile
            files = glob_all_src_files(target_directory)
        else:
            # XXX
            # files = [os.path.join(target_directory, file) for file in files]
            files = [os.path.join(abs_path_target_dir, file) for file in files]
            # files = [file for file in files]

        if len(files) == 0:
            logger.error("❌ No files in %s.", target_directory)
            row['Formatting'] = 0
            row['Linting'] = 0
            row['Build'] = 0
            row['Tests'] = 0
            row['Notes'] = f"❌ No files in {target_directory}."
            status = 1
        else:
            # Header checks
            files_missing_header = [
                file for file in files if not header_check(file)
            ]
            files_with_header = [file for file in files if header_check(file)]
            header = null_dict_header()
            if len(files_with_header) == 0:
                logger.error(
                    '❌ No header provided in any file in %s.', target_directory
                )
                # logger.error('All files: %s', ' '.join(files))
                row['Header'] = 0
                row['Formatting'] = 0
                row['Linting'] = 0
                row['Build'] = 0
                row['Tests'] = 0
                all_files = ' '.join(files)
                row[
                    'Notes'
                ] = f'❌ No header provided in any file in {target_directory}.'
                status = 1
            else:
                row['Header'] = 1
                header = dict_header(files_with_header[0])

            logger.info('Start %s', identify(header))
            logger.info(
                'All files: %s', ' '.join([os.path.basename(f) for f in files])
            )
            files_missing_header = [
                file for file in files if not header_check(file)
            ]
            row['Author'] = header['github'].replace('@', '').lower()
            partners = (
                header['partners']
                .replace(',', ' ')
                .replace('@', '')
                .lower()
                .split()
            )

            for num, name in enumerate(partners, start=1):
                key = f'Partner{num}'
                if num > 3:
                    break
                row[key] = name
            if len(partners) > 3:
                row['PartnerN'] = ';'.join(partners[3:])

            if len(files_missing_header) != 0:
                file_paths = [
                    p.absolute()
                    for p in map(pathlib.Path, files_missing_header)
                ]
                short_names = [
                    pathlib.Path(p.parts[-2]).joinpath(
                        pathlib.Path(p.parts[-1])
                    )
                    for p in file_paths
                ]
                files_missing_header_str = ', '.join(map(str, short_names))
                logger.warning(
                    'Files missing headers: %s', files_missing_header_str
                )
                row['Notes'] = (
                    row['Notes']
                    + f'❌Files missing headers: {files_missing_header_str}\n'
                )
                status = 1
            # Check if files have changed
            if base_directory:
                count = 0
                for file in files:
                    diff = strip_and_compare_files(
                        file, os.path.join(base_directory, file)
                    )
                    if len(diff) == 0:
                        count += 1
                        logger.error('No changes made in file %s.', file)
                if count == len(files):
                    logger.error('No changes made ANY file. Stopping.')
                    sys.exit(1)
            else:
                logger.debug('Skipping base file comparison.')

            # Format
            if do_format_check:
                count = 0
                for file in files:
                    try:
                        diff = format_check(file)
                        if len(diff) != 0:
                            logger.warning(
                                '❌ Formatting needs improvement in %s.',
                                os.path.basename(file),
                            )
                            logger.info(
                                'Please make sure your code conforms to the Google C++ style.'
                            )
                            logger.debug('\n'.join(diff))
                            row['Notes'] = (
                                row['Notes']
                                + f'❌ Formatting needs improvement in {os.path.basename(file)}.\n'
                            )
                            status = 1
                        else:
                            logger.info(
                                '✅ Formatting passed on %s',
                                os.path.basename(file),
                            )
                            count += 1
                    except ChildProcessError:
                        logger.warning('❌ clang-format is not executable')
                        row['Notes'] = (
                            row['Notes'] + '❌ clang-format is not executable\n'
                        )
                        status = 1
                row['Formatting'] = f'{count}/{len(files)}'
            else:
                row['Formatting'] = 'Skipped'

            # Lint
            if do_lint_check:
                count = 0
                for file in files:
                    lint_warnings = lint_check(
                        file, tidy_options, skip_compile_cmd
                    )
                    if len(lint_warnings) != 0:
                        logger.warning(
                            '❌ Linter found improvements in %s.',
                            os.path.basename(file),
                        )
                        logger.debug('\n'.join(lint_warnings))
                        row['Notes'] = (
                            row['Notes']
                            + f'❌ Linter found improvements in {os.path.basename(file)}.\n'
                        )
                        status = 1
                    else:
                        logger.info(
                            '✅ Linting passed in %s', os.path.basename(file)
                        )
                        count += 1
                row['Linting'] = f'{count}/{len(files)}'
            else:
                row['Linting'] = 'Skipped'
            # Unit tests
            # We don't know if there are unit tests in this project
            # or not. We'll assume there are and then check to see
            # if an output file was created.
            if do_unit_tests:
                logger.info('✅ Attempting unit tests')
                unit_test_output_file = "test_detail.json"
                # XXX
                # make_unittest(target_directory, output_file=unit_test_output_file)
                if not make_unittest(
                    abs_path_target_dir, output_file=unit_test_output_file
                ):
                    status = 1
                # make_unittest('.', output_file=unit_test_output_file)
                unit_test_output_path = os.path.join(
                    target_directory, unit_test_output_file
                )
                if not os.path.exists(unit_test_output_path):
                    unit_test_output_path = os.path.join(
                        '.', unit_test_output_file
                    )

                if os.path.exists(unit_test_output_path):
                    logger.info('✅ Unit test output found')
                    with open(
                        unit_test_output_path, 'r', encoding='UTF-8'
                    ) as json_fh:
                        unit_test_results = json.load(json_fh)
                        total_tests = unit_test_results['tests']
                        failures = unit_test_results.get('failures', 0)
                        passed_tests = total_tests - failures
                        if failures > 0:
                            logger.error(
                                '❌ One or more unit tests failed (%d/%d)',
                                passed_tests,
                                total_tests,
                            )
                        else:
                            logger.info('✅ Passed all unit tests')
                        row['UnitTests'] = f'{passed_tests}/{total_tests}'
                        row['UnitTestNotes'] = ""
                        for test_suite in unit_test_results['testsuites']:
                            name = test_suite['name']
                            for inner_suite in test_suite['testsuite']:
                                inner_name = inner_suite['name']
                                if 'failures' in inner_suite:
                                    for fail in inner_suite['failures']:
                                        this_fail = fail['failure']
                                        unit_test_note = (
                                            f'{name}:{inner_name}:{this_fail}\n'
                                        )
                                        row['UnitTestNotes'] = (
                                            row['UnitTestNotes']
                                            + unit_test_note
                                        )
                                        logger.error('❌ %s', unit_test_note)
            else:
                row['UnitTestNotes'] = "Unit tests disabled."
            main_src_file = None
            for file in files:
                if has_main_function(file):
                    short_file = os.path.basename(file)
                    if not main_src_file:
                        main_src_file = file
                        logger.info('Main function found in %s', short_file)
                        row['Notes'] = (
                            row['Notes']
                            + f'Main function found in {short_file}\n'
                        )
                    else:
                        logger.warning(
                            '❌ Extra main function found in %s', short_file
                        )
                        row['Notes'] = (
                            row['Notes']
                            + f'❌ Extra main function found in {short_file}\n'
                        )
            if not main_src_file:
                # This is going to use long paths
                files_str = ', '.join(files)
                logger.warning(
                    '❌ No main function found in files: %s', files_str
                )
                row['Notes'] = (
                    row['Notes']
                    + f'❌ No main function found in files: {files_str}\n'
                )

            # Clean, Build, & Run
            # XXX
            # if main_src_file and make_build(target_directory):
            # if main_src_file and make_build('.'):
            if main_src_file and make_build(abs_path_target_dir):
                logger.info('✅ Build passed')
                row['Build'] = 1
                # Run
                program_name = os.path.join(
                    os.path.dirname(os.path.abspath(main_src_file)),
                    program_name,
                )
                run_stats = run(program_name)
                # passed tests / total tests
                test_notes = f'{sum(run_stats)}/{len(run_stats)}'
                if all(run_stats):
                    logger.info('✅ All test runs passed')
                else:
                    logger.error('❌ One or more runs failed (%s)', test_notes)
                    row['Notes'] = (
                        row['Notes'] + '❌ One or more test runs failed\n'
                    )
                    status = 1
                row['Tests'] = test_notes
            else:
                logger.error('❌ Build failed')
                row['Build'] = 0
                row['Notes'] = row['Notes'] + '❌ Build failed\n'
                row['Tests'] = '0/0'
                status = 1
            logger.info('End %s', identify(header))
        outcsv.writerow(row)
    sys.exit(status)
