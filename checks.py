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

""" All the different checks needed to help a student turn in a perfect CPSC 120 lab. """

import sys
import os.path
from logger import setup_logger
from ccsrcutilities import lint_check, format_check

# from assessment import make_build
import lab_config as cfg

from parse_header import dict_header, header_keys


def header_check(file):
    """ Check file's header if it conforms to the standard given \
    in the example in the body of the function. Returns True if \
    the header is good. """
    # https://docs.google.com/document/d/17WkDlxO92zpb26pYM1NIACPcMWtCOlKO7WCrWC6YxRo/edit#
    # Example C++ header
    # // Michael Shafae
    # // mshafae@csu.fullerton.edu
    # // @mshafae
    # // Partners: @peteranteater, @ivclasers

    # return true if header is good
    # pylint: disable-next=unused-variable
    status, header = get_header_and_check(file)
    return status


def get_header_and_check(file_path, comments_startwith='//'):
    """ Check file's header if it conforms to the standard given \
    in the example in the body of the function. Returns True if \
    the header is good. """
    # https://docs.google.com/document/d/17WkDlxO92zpb26pYM1NIACPcMWtCOlKO7WCrWC6YxRo/edit#
    # Example C++ header
    # // Michael Shafae
    # // mshafae@csu.fullerton.edu
    # // @mshafae
    # // Partners: @peteranteater, @ivclasers

    header = dict_header(file_path, comments_startwith=comments_startwith)
    status = True
    missing_keys = list(set(header_keys) - set(header.keys()))
    logger = setup_logger()
    if missing_keys:
        status = False
        logger.warning('%s: missing %s fields', file_path, ', '.join(missing_keys))
    return (status, header)


def run_header_check(files):
    """Main function; process each file given through get_header_and_check."""
    logger = setup_logger()
    status = 0
    comments_startwith = '//'
    if comments_startwith == '#':
        # Python
        style_url = (
            'https://docs.google.com/document/d/'
            '1OgC3_82oZHpTvoemGXu84FAdnshve4BCvtwaXZEJ9FY/edit?usp=sharing'
        )
    else:
        # C++
        style_url = (
            'https://docs.google.com/document/d/'
            '17WkDlxO92zpb26pYM1NIACPcMWtCOlKO7WCrWC6YxRo/edit?usp=sharing'
        )
    status = 0
    for in_file in files:
        logger.info('Check header for file: %s', in_file)
        has_header, header_d = get_header_and_check(in_file, comments_startwith)
        if not has_header:
            logger.warning('Header is malformed or missing.')
            logger.warning('Could not find a header in the file.')
            logger.warning(
                'Information about header formatting is at %s', style_url
            )
            # only set the status to fail if a bad header is encountered
            status = 1
        else:
            logger.info('Header found.')
            logger.info("Name: %s", header_d['name'])
            logger.info("Email: %s", header_d['email'])
            logger.info("GitHub Handle: %s", header_d['github'])
            logger.info("Partners: %s", header_d['partners'])

    sys.exit(status)


def run_format_check(files):
    """Main function; check the format of each file on the
    command line."""
    logger = setup_logger()
    # if len(sys.argv) < 2:
    #     logger.warning('Only %s arguments provided.', len(sys.argv))
    #     logger.warning('Provide a list of files to check.')
    status = 0
    for in_file in files:
        logger.info('Checking format for file: %s', in_file)
        if not os.path.exists(in_file):
            logger.debug('File %s does not exist. Continuing.', in_file)
            continue
        try:
            diff = format_check(in_file)
            if len(diff) != 0:
                logger.warning("Error: Formatting needs improvement.")
                diff_string = 'Contextual Diff\n' + '\n'.join(diff)
                logger.warning(diff_string)
                status = 1
                logger.error("🤯😳😤😫🤬")
                logger.error(
                    "Your formatting doesn't conform to the Google C++ style."
                )
                logger.error(
                    "Use the output from this program to help guide you."
                )
                logger.error("If you get stuck, ask your instructor for help.")
                logger.error(
                    "Remember, you can find the Google C++ style online "
                    "at https://google.github.io/styleguide/cppguide.html."
                )
            else:
                logger.info('😀 Formatting looks pretty good! 🥳')
        except ChildProcessError:
            logger.error('error: clang-format is not executable')
            logger.warning(
                'This command error indicates that your Linux system '
                'is not prepared for CPSC 120 labs.'
            )
            logger.warning(
                'The quickinstall.sh command was skipped, or produced'
                ' an error message that you did not notice.'
            )
            logger.warning(
                'Follow the instructions in the "Linux Setup" page in Canvas'
                ' to run the quickinstall.sh command.'
            )
    sys.exit(status)


def run_lint_check(files):
    """Check the given files to see if they conform to good programming
    practices using clang-tidy."""
    logger = setup_logger()
    status = 0
    for in_file in files:
        logger.info('Linting file: %s', in_file)
        if not os.path.exists(in_file):
            logger.debug('File %s does not exist. Continuing.', in_file)
            continue
        # Use global lint configuration
        tidy_opts = cfg.global_tidy_options_string
        lint_warnings = lint_check(in_file, tidy_opts)
        if len(lint_warnings) != 0:
            logger.error('Linter found improvements.')
            logger.warning('\n'.join(lint_warnings))
            status = 1
            logger.error("🤯😳😤😫🤬")
            logger.error("Use the output from this program to help guide you.")
            logger.error("If you get stuck, ask your instructor for help.")
            logger.error(
                "Remember, you can find the Google C++ style online "
                "at https://google.github.io/styleguide/cppguide.html."
            )
        else:
            logger.info('😀 Linting passed 🥳')
            logger.info('This is not an auto-grader.')
            logger.info(
                'Make sure you followed all the instructions and requirements.'
            )
    sys.exit(status)


# def run_make_build_check():
#     """ Main function; process all files from the command line. """
#     logger = setup_logger()
#     if len(sys.argv) < 2:
#         logger.warning('Only %s arguments provided.', len(sys.argv))
#         logger.warning('Provide a target directory to `make`.')
#         sys.exit(1)
#     status = 0
#     for target_dir in sys.argv[1:]:
#         logger.info("Checking build for %s", target_dir)
#         if make_build(target_dir):
#             logger.info('😀 Build passed 🥳')
#         else:
#             logger.error("🤯😳😤😫🤬")
#             logger.error('Build failed.')
#             logger.error('Double check your work and use the make command to build your project.')
#             status = 1
#             break
#     sys.exit(status)


def main():
    """Main function; looks at sys.argv and calls the appropriate function."""
    logger = setup_logger()
    if len(sys.argv) < 3:
        logger.error('Not enough arguments provided.')
        sys.exit(1)
    cmd = sys.argv[1]
    # There is a danger here with the variable files.
    # The definition of the files is based off of the repo's root
    # directory. We can get the absolute path however we only can do that if the path is 
    # correct at this point. Let's leave them as relative paths (strings) for now and see
    # if conversion to fully qualified paths is neceesary.
    files = []
    if sys.argv[2] == 'all':
        # All parts
        for index, part in enumerate(cfg.lab['parts']):
            part_name = f'part-{index+1}'
            for src_key in 'src header'.split():
                if len(part[src_key]):
                    l = [os.path.join(part_name, file_name) for file_name in part['src'].split()]
                    files += l
    else:
        # Just one part
        try:
            # This is really fragile
            part_num = int(sys.argv[2][-1])
        except ValueError as exception:
            logger.error(
                'The name of the part, %s, does not match the pattern "part-N".', sys.argv[2]
            )
            logger.error(str(exception))
            sys.exit(1)
        lab_config = cfg.lab['parts'][part_num - 1]
        files = lab_config['src'].split() + lab_config['header'].split()
    status = 1
    if cmd == 'format':
        run_format_check(files)
    elif cmd == 'lint':
        run_lint_check(files)
    elif cmd == 'header':
        run_header_check(files)
    else:
        logger.error('No such command %s. Exiting.', cmd)
    sys.exit(status)


if __name__ == '__main__':
    main()
