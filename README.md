# Predictive-Risk-Assessment-Framework
Design-stage risk intelligence and decision architecture for early-stage POCT device development
predictive-risk-assessment-framework/
  README.md
  LICENSE
  pyproject.toml
  .gitignore
  src/
    praf/
      __init__.py
      config/
        __init__.py
        defaults.py
        schemas.py
      domain/
        __init__.py
        activities.py
        domains.py
        natures.py
        categories.py
        indicators.py
      engine/
        __init__.py
        scorer.py
        aggregator.py
        classifier.py
        rules.py
        explainability.py
        audit_trail.py
      io/
        __init__.py
        loaders.py
        exporters.py
      cli/
        __init__.py
        main.py
  data/
    templates/
      indicator_library_template.csv
      weights_template.csv
    examples/
      example_inputs.json
  docs/
    iso/
      risk_management_approach.md
      scoring_method.md
  tests/
    test_scorer.py
    test_classifier.py
    test_pipeline.py
  scripts/
    generate_example_outputs.py

## Installation

```bash
pip install -e .
```

## Usage

Run the scoring pipeline on a JSON input file (see `data/examples/example_inputs.json`):

```bash
python -m praf.cli.main data/examples/example_inputs.json
```

Launch the interactive app:

```bash
streamlit run app.py
```

Regenerate the example output:

```bash
python scripts/generate_example_outputs.py
```

## Tests

```bash
pip install pytest
pytest
```
