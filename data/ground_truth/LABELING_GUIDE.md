# Redundancy labeling guide

Annotate one time interval for each candidate passage. Set `is_redundant` to `true` when the instructor's spoken text and the on-screen text in that interval convey substantially the same information. Exact wording is not required; equivalent paraphrases count as redundant.

Set `is_redundant` to `false` when on-screen text adds a distinct example, definition, detail, or visual representation that materially extends the speech. Do not label brief incidental word overlap as redundant.

Use the start and end timestamps of the shared content. Each interval must have non-negative numeric timestamps and `end_time` should be later than `start_time`.
