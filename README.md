# dirmig

Dead simple db migration tool for applying sql from a directory.

I made this for myself to manage a third-party package which ships a bunch of SQL migration files, but has no way to apply them.

## instructions

```sh
# install
pip install git+https://github.com/abe-winter/dirmig.git

# run missing migrations
export DATABASE_URL=postgres://...
dirmig suffix ./whatever/sqlfiles
# this will create metadata tables like dirmigv_suffix and dirmig_suffix

# get help
dirmig -h
```

## database support

- only tested on postgres, uses asyncpg

## wishlist

- [ ] pluggable backend (i.e. not just asyncpg)
- [ ] hashes of files
- [ ] some kind of 'undo' approach
- CI
  - [ ] lint
  - [ ] test
- [ ] a third party tool that I could use instead of writing my own

## better tools

If you know of a better tool that does this, file a PR pls to add it here.
