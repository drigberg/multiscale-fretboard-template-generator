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
![alt text](output/lines-with-strings.png)

**Frets as lines, without strings:**
![alt text](output/lines-without-strings.png)

**String/fret intersection points:**
![alt text](output/only-points.png)
