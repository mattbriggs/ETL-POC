# Assess API

## config

::: dita_etl.assess.config
    options:
      members:
        - AssessConfig
        - Shingling
        - ScoringWeights
        - Limits
        - Duplication

## structure

::: dita_etl.assess.structure
    options:
      members:
        - sectionize_markdown
        - sectionize_html
        - heading_ladder_valid

## features

::: dita_etl.assess.features
    options:
      members:
        - count_tokens
        - imperative_density
        - extract_features

## scoring

::: dita_etl.assess.scoring
    options:
      members:
        - score_topicization
        - score_risk

## predict

::: dita_etl.assess.predict
    options:
      members:
        - predict_topic_type

## dedupe

::: dita_etl.assess.dedupe
    options:
      members:
        - shingle_tokens
        - minhash_signature
        - jaccard_from_signatures
        - cluster_near_duplicates
