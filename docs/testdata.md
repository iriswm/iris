# Test data
A simple set of test data is provided:

* 5 users with usernames/passwords/roles: `admin`, `manager` and `worker1-3`.
* Capital letters `A` and `B` are process names.
* Letters from `a` to `d` are stations.
* Numbers from `1` to `9` are steps.
* Names `alpha`, `beta`, `gamma`, `omega`, `zeta` and `lamda` are items in
  different states of completion.

The secret key used for the dev data is:
`django-insecure-gs=xloqs7ztt*v)e_w=!moh+_vvfu25#_$c^yhdspv_wosx&om`.

## Completion status diagrams
In the diagrams below:

* commits are shown as `commit`,
* suspensions as `suspend`
* delays as `delay`
* In any of the previous options, a `+ note` shows the status has a note.

The data was created by hand. The dates start on 27 May 2023. Delays are 1000
days long. States are at least one second apart, ordered usually first by
station and then by position.

### alpha
```
a     A ----- 1 commit --- 2 commit --- 3 ----- 5
         \                                 /
          \                               /
b           - 4 delay  ------------------
```

### beta
```
a     A ----- 1 commit --- 2 commit --- 3 commit + note ----- 5 suspend
         \                                               /
          \                                             /
b           - 4 commit --------------------------------
```

### gamma
```
a     A ----- 1 commit --- 2 commit --- 3 commit ----- 5 commit
         \                                        /
          \                                      /
b           - 4 commit -------------------------
```

### omega
```
c                           - 7 -
                          /       \
a     B ------ 6 commit --         ------- 9
         \                \       /   /
d         \                 - 8 -    /
           \                        /
b            - 4 commit -----------
```

### zeta
```
c                           - 7 suspend + note -
                          /                      \
a     B ------ 6 commit --                        ------- 9
         \                \                      /   /
d         \                 - 8 delay + note ---    /
           \                                       /
b            - 4 commit + note -------------------
```

### lambda
```
c                                  - 7 commit + note -
                                 /                     \
a     B ------ 6 commit + note --                       ----- 9 commit + note
         \                       \                     /   /
d         \                        - 8 commit + note -    /
           \                                             /
b            - 4 commit + note -------------------------
```
