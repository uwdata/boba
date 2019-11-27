# Multiverse of the Hurricane Dataset

In this example, we implemented the specification curve analysis on Jung's hurricane study,
described in the seminal paper of Simonsohn et al. 

Useful URLs:
- Specification curve paper by Simonsohn et al.: 
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2694998

- The appendix of the specification curve paper:
http://urisohn.com/sohn_files/wp/wordpress/wp-content/uploads/Supplement-Specification-Curve-2019-10-29.pdf

- STATA code implementing the specification curve analysis:
http://urisohn.com/sohn_files/files/Specification%20Curve.zip

- Hurricane paper by Jung et al.:
https://doi.org/10.1073/pnas.1402786111

- Supporting material of the hurricane paper:
https://www.pnas.org/content/suppl/2014/05/30/1402786111.DCSupplemental


### Augmenting the Dataset

Following the description in Uri Simonsohn's STATA code, we augmented the original
hurricane dataset via the following steps:

- We added the two outliers excluded in Jung's study - Katrina and Audrey.
- We replaced the femininity ratings (MasFem) with the average ratings from 32 MTurkers,
collected using the same scale as described in Jung's paper. Uri Simonsohn kindly
provided the MTurk ratings to us.
- Accordingly, we also updated the binary gender indicator, so a femininity rating higher
than 6 is categorized as female.
- We updated the normalized damage to 2019 dollar values, using the same website as
Jung et al: http://www.icatdamageestimator.com/commonsearch
- We added a column of highest wind speed (mph) using the Wikipedia as the data source.

### Notes

1. Simonsohn generated 1728 universes, while we created only 864 universes.
We wrote our multiverse specification according to the definition in page 4 of Simonsohn's appendix.
But in their actual implementation, Simonsohn separated the first decision (of size 6)
into a cross product of two decisions (3x4), thus doubling the size of the final multiverse.

2. As we used a slightly different dataset than the one used by Jung et al., we did not obtain the same result when using the original specification in Jung's study.

3. About 40 universes, all fitting a negative binomial model, will fail because
of this error:
```
Error in glm.fitter(x = X, y = Y, w = w, etastart = eta, offset = offset,  : 
  NA/NaN/Inf in 'x'
Calls: glm.nb -> glm.fitter
```
The helper script `debug_count.py` outputs which universes had failed.
