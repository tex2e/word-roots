# word-roots

```
$ python3 find_word_roots.py telecommuter --tree

┌────────────────── far, distant, complete
│    ┌───────────── together, common
│    │   ┌───────── change
│    │   │   ┌───── a person who does an action
│    │   │   ├───── action or process
│    │   │   ├───── more
tele com mut er

$ python3 find_word_roots.py unilateral

┌───────────── one, single
│   ┌───────── side
│   │     ┌─── relating to
uni later al

```

## TODO

expected:

```
$ python3 find_word_roots.py magnanimous

┌────────────── great, large
│    ┌───────── life, spirit
│    │    ┌──── full of
magn anim ous

```

actual:

```
$ python3 find_word_roots.py magnanimous

┌─────────────── great, large
│       ┌─────── not, without
│       │  ┌──── full of
magna n im ous

```
