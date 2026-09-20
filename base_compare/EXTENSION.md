# Study B extension: are the norm items normative, or merely keyed?

Written 2026-09-21T03:05+09:00, after Study B's confirmatory results were known
and in response to a pre-submission referee. Not part of the frozen Study B
pre-registration. The question, the method and the reading of each possible
outcome are fixed here before the extension is run.

## The challenge

Four non-subject coders recover the designated norm option from item text alone
(29/30 each), and five pre-trained models select it 81-100% of the time without
any instruction following. Both facts support the manuscript's reading, that the
norm is legible in the written record. They equally support a deflationary one:
that the 30 norm-transparent items are *keyed* items with a discoverable correct
answer, so H2's gradient measures keyedness rather than normativity. Nothing in
the study as it stands separates these.

## The test

The 120 habitus items carry no designated option and no policy anchor, yet 30 of
the 81 valid ones reach seven-model consensus. Score the same ten Study B models
on those 120 items with the identical frozen instrument, and ask whether
pre-trained determinacy explains subject consensus outside the codified layer.

Determinacy of a pre-trained model on an item is the mean, over the four
rotations, of the probability mass it places on its own top option among the four
letters. This is defined without reference to any designated option, so it
applies to habitus items.

## Readings, fixed before running

- **Deflationary outcome.** The 30 uncodified-consensus items are also items on
  which pre-trained models are already decided (determinacy clearly higher than
  on the 51 non-consensus items). Then "consensus" tracks "the item has a
  probable answer" throughout the battery, the codified/uncodified distinction is
  not doing the work §8.1 claims, and the manuscript must say so and retire the
  normative reading of H2 in favour of a keyedness reading.
- **Normative outcome.** The 30 uncodified-consensus items show determinacy no
  higher than the rest, while the seven subjects nevertheless converge on them.
  Then subject consensus is not reducible to base-model determinacy, the
  keyedness objection fails outside the codified layer, and the distinction
  between codified and uncodified consensus is doing real work.
- **Mixed outcome.** Any intermediate pattern is reported as such, with the
  effect size, and the manuscript states that the two readings are not separated.

Test: Mann-Whitney U on determinacy, 30 consensus vs 51 non-consensus habitus
items, two-sided, per pre-trained model; and the same for the norm layer versus
the habitus layer to quantify how much more keyed the norm items are.

Reported whatever it shows.
