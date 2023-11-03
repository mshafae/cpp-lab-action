#!/usr/bin/env python3

"""A lab configuration file."""

from datetime import date

# A list of target names in the order of the lab's parts.
targets = ['judge', 'schedule']

lab = {
    # Due date for labs
    'mon_duedate': date(2023, 11, 15),
    'tues_duedate': date(2023, 11, 8),
    'wed_duedate': date(2023, 11, 8),
    'num_parts': len(targets),
    'makefile_name': 'Makefile',
    # Prefix Makefiles with a period to hid them
    'hidden_makefiles': False,
    # Configuration of target, source files, and header files for each part. These are the files
    # that will be checked for headers, format, and lint.
    # other_src and other_header are files that are needed for building and are not graded/assessed.
    # Unit tests are always built as:
    # $(CXX) $(GTESTINCLUDE) $(LDFLAGS) -o unittest $(TARGET)_unittest.cc $(TARGET)_functions.o
    # where the unit tests are in $(TARGET)_unittest.cc with the
    # sole dependency on $(TARGET)_functions.o
    'parts': [
        {
            'target': targets[0],
            'src': f'{targets[0]}.cc',
            'header': '',
            'other_src': '',
            'other_header': '',
            'test_main': 'run_p1',
        },
        {
            'target': targets[1],
            'src': f'{targets[1]}.cc',
            'header': '',
            'other_src': '',
            'other_header': '',
            'test_main': 'run_p2',
        },
    ],
}

# The list of disabled checks. (Note: all checks are enabled and then disabled, one by one.)
# List of clang tidy checks: https://clang.llvm.org/extra/clang-tidy/checks/list.html
# pylint: disable-next=invalid-name
global_tidy_checks = (
    '-checks="*,'
    '-misc-unused-parameters,'
    '-modernize-use-trailing-return-type,'
    '-google-build-using-namespace,'
    '-cppcoreguidelines-avoid-magic-numbers,'
    '-readability-magic-numbers,'
    '-fuchsia-default-arguments-calls,'
    '-llvmlibc-callee-namespace,'
    '-llvmlibc-implementation-in-namespace,'
    '-llvm-header-guard,'
    '-bugprone-easily-swappable-parameters,'
    '-llvm-else-after-return,'
    '-readability-else-after-return,'
    '-readability-simplify-boolean-expr,'
    '-altera-unroll-loops,'
    '-altera-id-dependent-backward-branch,'
    "-bugprone-narrowing-conversions,"
    "-cppcoreguidelines-narrowing-conversions,"
    '"'
)
# '-clang-analyzer-deadcode.DeadStores,'\
# '-bugprone-exception-escape,'\
# '-cert-err58-cpp,'\
# '-fuchsia-statically-constructed-objects,'\
# '-cert-msc32-c,'\
# '-cert-msc51-cpp,'\
# '-google-runtime-references"'\

# Check options which conform to the Google C++ style guide,
# https://google.github.io/styleguide/cppguide.html.
# Clang documentation:
# https://clang.llvm.org/extra/clang-tidy/checks/readability/identifier-naming.html
# pylint: disable-next=invalid-name
global_tidy_config = (
    '-config="{CheckOptions: ['
    '{key: readability-identifier-naming.ClassCase, value: CamelCase}, '
    '{key: readability-identifier-naming.ClassMemberCase, value: lower_case}, '
    '{key: readability-identifier-naming.ConstexprVariableCase, value: CamelCase}, '
    '{key: readability-identifier-naming.ConstexprVariablePrefix, value: k}, '
    '{key: readability-identifier-naming.EnumCase, value: CamelCase}, '
    '{key: readability-identifier-naming.EnumConstantCase, value: CamelCase}, '
    '{key: readability-identifier-naming.EnumConstantPrefix, value: k}, '
    '{key: readability-identifier-naming.GlobalFunctionCase, value: CamelCase}, '
    '{key: readability-identifier-naming.FunctionCase, value: CamelCase}, '
    '{key: readability-identifier-naming.GlobalConstantCase, value: CamelCase}, '
    '{key: readability-identifier-naming.GlobalConstantPrefix, value: k}, '
    '{key: readability-identifier-naming.StaticConstantCase, value: CamelCase}, '
    '{key: readability-identifier-naming.StaticConstantPrefix, value: k}, '
    '{key: readability-identifier-naming.StaticVariableCase, value: lower_case}, '
    '{key: readability-identifier-naming.MacroDefinitionCase, value: UPPER_CASE}, '
    '{key: readability-identifier-naming.MacroDefinitionIgnoredRegexp, '
    'value: \'^[A-Z]+(_[A-Z]+)*_$\'}, '
    '{key: readability-identifier-naming.MemberCase, value: lower_case}, '
    '{key: readability-identifier-naming.PrivateMemberSuffix, value: _}, '
    '{key: readability-identifier-naming.PublicMemberSuffix, value: \'\'}, '
    '{key: readability-identifier-naming.NamespaceCase, value: lower_case}, '
    '{key: readability-identifier-naming.ParameterCase, value: lower_case}, '
    '{key: readability-identifier-naming.TypeAliasCase, value: CamelCase}, '
    '{key: readability-identifier-naming.TypedefCase, value: CamelCase}, '
    '{key: readability-identifier-naming.VariableCase, value: lower_case}, '
    '{key: readability-identifier-naming.IgnoreMainLikeFunctions, value: 1}'
    ']}"'
)

# pylint: disable-next=invalid-name
tidy_compiler_options = (
    '-std=c++17 -I /opt/local/include -I /usr/local/include '
    '-nostdinc++ -I/usr/include/c++/11 -I/usr/include/x86_64-linux-gnu/c++/11'
)


# Concatenate clang's checks and options into a single string ready to
# be used as a command line option.
global_tidy_options_string = f'{global_tidy_checks} {global_tidy_config}'

global_makefile = {
    'CXX': 'clang++',
    'CXXFLAGS': '-g -O3 -Wall -pedantic -pipe -std=c++17',
    'LDFLAGS': '-g -O3 -Wall -pedantic -pipe -std=c++17',
    # Linting & Formatting tests
    'do_format_check': True,
    'do_lint_check': True,
    # clang-tidy options, can be overridden per part
    'tidy_opts': global_tidy_options_string,
    'skip_compile_cmd': False,
    # Google Test & Google Mock
    'do_unit_tests': False,
    'gtest_dependencies': '$(TARGET)_functions.o $(TARGET)_unittest.cc',
    # pylint: disable-next=line-too-long
    'gtest_compile_cmd': '@$(CXX) $(GTESTINCLUDE) $(LDFLAGS) -o unittest $(TARGET)_unittest.cc $(TARGET)_functions.o $(GTESTLIBS)',
    'gtest_run': '@./unittest --gtest_output=$(GTEST_OUTPUT_FORMAT):$(GTEST_OUTPUT_FILE)',
    'GTEST_OUTPUT_FORMAT': 'json',
    'GTEST_OUTPUT_FILE': 'test_detail.json',
    # Doxygen
    'DOXYGEN': 'doxygen',
    'DOCDIR': 'doc',
    'tidyopts': global_tidy_options_string,
    # Linux specific settings
    # pylint: disable-next=line-too-long
    'linux_CXXFLAGS': '-D LINUX -nostdinc++ -I/usr/include/c++/11 -I/usr/include/x86_64-linux-gnu/c++/11',
    'linux_LDFLAGS': '-L /usr/lib/gcc/x86_64-linux-gnu/11',
    'linux_sed': 'sed',
    # pylint: disable-next=line-too-long
    'linux_GTESTINCLUDE': '-D LINUX -nostdinc++ -I/usr/include/c++/11 -I/usr/include/x86_64-linux-gnu/c++/11',
    'linux_GTESTLIBS': '-L /usr/lib/gcc/x86_64-linux-gnu/11 -lgtest -lgtest_main -lpthread',
    # Darwin (macOS) specific settings assuming MacPorts, not Homebrew
    'darwin_CXXFLAGS': '-D OSX -nostdinc++ -I/opt/local/include/libcxx/v1',
    # pylint: disable-next=line-too-long
    'darwin_LDFLAGS': '-L/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib -L/opt/local/lib/libcxx',
    'darwin_sed': 'gsed',
    'darwin_GTESTINCLUDE': '-I/opt/local/include -I/opt/local/src/googletest',
    'darwin_GTESTLIBS': '-L/opt/local/lib -lgtest -lgtest_main',
}


makefiles = [global_makefile.copy() for i in range(len(targets))]

# Specific Makefile settings for each lab part.
# If a lab has unit tests, set 'do_unit_tests' to True
makefiles[0].update(
    {
        'do_unit_tests': False,
        'do_format_check': True,
        'do_lint_check': True,
    }
)

makefiles[1].update(
    {
        'do_unit_tests': False,
        'do_format_check': True,
        'do_lint_check': True,
    }
)

# Merge the makefile dict into the lab_dict's part's dictionary
for lab_dict, makefile in zip(lab['parts'], makefiles):
    lab_dict.update(makefile)

def main():
    """ A function to access any value within the lab's configuration given a series of keys for use with scripts and workflows. Returns 0 if executed without a problem. """
    import sys
    if len(sys.argv) > 1:
        primary_key = sys.argv[1]
        if primary_key == 'gradedsrc':
            allsrc = ''
            for p in lab['parts']:
                allsrc += '{} {} '.format(p['src'], p['header'])
            value = allsrc
        elif primary_key == 'makefile_name':
            if lab['hidden_makefiles']:
                value = '.{}'.format(lab['makefile_name'])
            else:
                value = lab['makefile_name']
        elif primary_key == 'parts' and len(sys.argv) >= 4:
            try:
                part_number = int(sys.argv[2])
            except ValueError as exception:
                sys.exit(1)
            sub_key = sys.argv[3]
            try:
                parts_list = lab[primary_key]
            except KeyError as exception:
                sys.exit(1)
            try:
                part = parts_list[part_number]
            except IndexError as exception:
                sys.exit(1)
            try:
                value = part[sub_key]
            except KeyError as exception:
                sys.exit(1)
        else:
            try:
                value = lab[primary_key]
            except KeyError as exception:
                sys.exit(1)
    print(value)
    sys.exit(0)


if __name__ == '__main__':
    main()
