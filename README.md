# multiscale-fretboard-template-generator

This repo contains a script for generating multiscale fret templates!

## Usage

1. Copy `config.example.yml` to a new file named `config.yml`
2. Update the values for your use-case, with all measurements in millimeters
3. Run the script below and check your output folder!

```bash
python3 -m pipenv run generator
```

## Output

The script generates three templates:

**Frets as lines, with outer strings:**
![Frets as lines, with strings](examples/lines-with-strings.png)

**Frets as lines, without strings:**
![Frets as lines, without strings](examples/lines-without-strings.png)

**String/fret intersection points:**
![String/fret intersection points](examples/only-points.png)
