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

Dose is calculated separately for different population age groups.
This table defines bounds of each group and some groups' characteristics.

|Column|Description|Dimension|
| --- | --- | --- |
|`id`|Age group unique identifier|1|
|`lower_age`|Lower limit of age group|years|
|`upper_age`|Upper limit of age group|years|
|`respiration_rate`|Average respiration rate of the group|m^3/s|
|`daily_metabolic_cost`|Avertage daily metabolic cost of the group|kcal/day|

## Food

This table simply defines identifiers of food categories which other tables use
as foreign key.

|Column|Description|Dimension|
| --- | --- | --- |
|`id`|Food category unique identifier|1|
|`food category`|Short food category name such as *meat*, *milk*, etc|text|

## Accumulation factors

Nuclides are being accumulated in food.
This table defines values needed to model that process.

|Column|Description|Dimension|
| --- | --- | --- |
|`id`|Accumulation factor unique identifier|1|
|`nuclide`|Nuclide name such as *Cs-137*, etc[^1]|text|
|`accumulation source`|*soil* or *atmosphere*|text|
|`food_id`|Food category unique identifier|1|
|`accumulation_factor`|Accumulation factor for given nuclide, source and food|m^2/kg[^2] or m^2/litre[^3]|

[^1]: Note that nuclides names in this table should correspond to ones in [Nuclides](#Nuclides) table.
[^2]: For solid food such as meat, vegetables.
[^3]: For liquied food such as milk.

## Roughness

## Diffusion coefficients

## Nuclides

