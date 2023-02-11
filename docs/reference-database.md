# Reference database

Reference database file is `sqlite` database made with `dataset` package.
For now the best way to make it is to do it manually using `dataset`.
I will now desctibe its' architecture.

DB has 6 tables:
```python
>>> db.tables
['accumulation_factors', 'age_groups', 'diffusion_coefficients', 'food', 'nuclides', 'roughness']
```

## Age groups

|Column|Description|Dimension|
| --- | --- |
|`id`|Age group unique identifier|1|
|`lower_age`|Lower limit of age group|years|
|`upper_age`|Upper limit of age group|years|
|`respiration_rate`|Average respiration rate of the group|m^3/s|
|`daily_metabolic_cost`|Avertage daily metabolic cost of the group|kcal/day|

## Food

## Roughness

## Diffusion coefficients

## Accumulation factors

## Nuclides


