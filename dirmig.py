#!/usr/bin/env python3
"dirmig -- apply migrations from a directory"

import argparse, asyncio, os, re, logging, glob, importlib
import asyncpg

logger = logging.getLogger(__name__)

async def migrate_mig_table(cx, args):
    "create / migrate dirmig_ and dirmigv_ tables, i.e. migration metadata"
    async with cx.transaction():
        await cx.execute(f'create table if not exists dirmigv_{args.name} (version int primary key, created timestamp with time zone default now())')
        cur_version = await cx.fetchval(f'select max(version) from dirmigv_{args.name}')
        if cur_version is None:
            logger.info('[dirmig-meta] performing null migration')
            await cx.execute(f'create table if not exists dirmig_{args.name} (path text primary key, created timestamp with time zone default now())')
            await cx.execute(f'insert into dirmigv_{args.name} (version) values (1)')

async def migrated(cx, args):
    "return set of (relative) migration paths that have already been applied"
    rows = await cx.fetch(f'select path from dirmig_{args.name}')
    return {row['path'] for row in rows}

def resolve_path(args):
    "do modpath resolution on directory if necessary"
    if not args.modpath:
        return args.path
    module, _, subpath = args.path.partition('.')
    found = importlib.machinery.PathFinder.find_spec(module)
    assert found
    logger.debug('found modpath %s %s in %s', module, subpath, found)
    # warning: submodule_search may not always be present; a single-file package with embedded datafiles for example
    return os.path.join(found.submodule_search_locations[0], subpath)

async def asyncmain(args):
    "async entrypoint. sets up migration metadata, searches migration folder, runs missing migrations"
    cx = await asyncpg.connect(args.dsn)
    await migrate_mig_table(cx, args)

    # list migration files + apply unapplied in sort-order
    path = resolve_path(args)
    files = sorted(fname for fname in os.listdir(path) if os.path.splitext(fname)[-1] == args.ext)
    async with cx.transaction():
        exists = await migrated(cx, args)
        for fname in files:
            if fname in exists:
                logger.debug('[dirmig] skipping already-applied %s', fname)
                continue
            stmt = open(os.path.join(path, fname)).read()
            logger.info('[dirmig] running %s', fname)
            await cx.execute(stmt)
            await cx.execute(f'insert into dirmig_{args.name} (path) values ($1)', fname)

def main():
    "set up args and hand off to async"
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('name', help="suffixed to table name")
    p.add_argument('path', help="path to migrations directory")
    p.add_argument('-m', '--modpath', help="path is relative to a python module. if this is set, path should look like 'modname.dir/dir'", action='store_true')
    p.add_argument('--ext', help="file extension to run", default='.sql')
    p.add_argument('--dsn', default=os.environ.get('DATABASE_URL'))
    p.add_argument('-l', '--level', help="log level", default='info')
    args = p.parse_args()

    if not re.match(r'^\w{3,8}$', args.name):
        raise TypeError(f'name must be alpha of len 3-8, you put {args.name}')

    logging.basicConfig(level=getattr(logging, args.level.upper()))
    asyncio.run(asyncmain(args))

if __name__ == '__main__':
    main()
