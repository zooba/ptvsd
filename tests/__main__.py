import os
import os.path
import subprocess
import sys
import unittest


TEST_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(TEST_ROOT)


def convert_argv(argv):
    help  = False
    quick = False
    network = True
    lint = False
    runtests = True
    args = []
    modules = set()
    for arg in argv:
        if arg == '--quick':
            quick = True
            continue
        elif arg == '--full':
            quick = False
            continue
        elif arg == '--network':
            network = True
            continue
        elif arg == '--no-network':
            network = False
            continue
        elif arg == '--coverage':
            runtests = 'coverage'
            continue
        elif arg == '--lint':
            lint = True
            continue
        elif arg == '--lint-only':
            lint = True
            runtests = False
            break

        # Unittest's main has only flags and positional args.
        # So we don't worry about options with values.
        if not arg.startswith('-'):
            # It must be the name of a test, case, module, or file.
            # We convert filenames to module names.  For filenames
            # we support specifying a test name by appending it to
            # the filename with a ":" in between.
            mod, _, test = arg.partition(':')
            if mod.endswith(os.sep):
                mod = mod.rsplit(os.sep, 1)[0]
            mod = mod.rsplit('.py', 1)[0]
            mod = mod.replace(os.sep, '.')
            arg = mod if not test else mod + '.' + test
            modules.add(mod)
        elif arg in ('-h', '--help'):
            help = True
        args.append(arg)

    if runtests:
        env = {}
        if network:
            env['HAS_NETWORK'] = '1'
        # We make the "executable" a single arg because unittest.main()
        # doesn't work if we split it into 3 parts.
        cmd = [sys.executable + ' -m unittest']
        if not modules and not help:
            # Do discovery.
            quickroot = os.path.join(TEST_ROOT, 'ptvsd')
            if quick:
                start = quickroot
            elif sys.version_info[0] != 3:
                start = quickroot
            else:
                start = PROJECT_ROOT
            cmd += [
                'discover',
                '--top-level-directory', PROJECT_ROOT,
                '--start-directory', start,
            ]
        args = cmd + args
    else:
        args = env = None
    return args, env, runtests, lint


def fix_sys_path():
    pydevdroot = os.path.join(PROJECT_ROOT, 'ptvsd', 'pydevd')
    if not sys.path[0] or sys.path[0] == '.':
        sys.path.insert(1, pydevdroot)
    else:
        sys.path.insert(0, pydevdroot)


def check_lint():
    print('linting...')
    args = [
        sys.executable,
        '-m', 'flake8',
        '--ignore', 'E24,E121,E123,E125,E126,E221,E226,E266,E704,E265',
        '--exclude', 'ptvsd/pydevd',
        PROJECT_ROOT,
    ]
    rc = subprocess.call(args)
    if rc != 0:
        print('...linting failed!')
        sys.exit(rc)
    print('...done')


def run_tests(argv, env, coverage=False):
    print('running tests...')
    if coverage:
        args = [
            sys.executable,
            '-m', 'coverage',
            'run',
            '--include', 'ptvsd/*.py',
            '--omit', 'ptvsd/pydevd/*.py',
            '-m', 'unittest',
        ] + argv[1:]
        rc = subprocess.call(args, env=env)
        if rc != 0:
            print('...coverage failed!')
            sys.exit(rc)
        print('...done')
    else:
        os.environ.update(env)
        unittest.main(module=None, argv=argv)


if __name__ == '__main__':
    argv, env, runtests, lint = convert_argv(sys.argv[1:])
    fix_sys_path()
    if lint:
        check_lint()
    if runtests:
        if '--start-directory' in argv:
            start = argv[argv.index('--start-directory') + 1]
            print('(will look for tests under {})'.format(start))
        run_tests(
            argv,
            env,
            coverage=(runtests == 'coverage'),
        )
