# Hausarbeit PHY-B

Es sollen sensorbasiert ähnlich einer Fitnessuhr verschiedene Sportübungen sowie deren Anzahl erkannt werden.
Benutzt werden sollen der Beschleunigungssensor und das Gyroskop des IMU-6050.\\
Mein Lösungsansatz gliedert sich in mehrere Stufen:
die Rohdaten aus dem IMU-6050 sollten durch einen mehrdimensionalen Kalman-Filter bereinigt werden.
Die bereinigten Daten werden mit dem K-Means Algorithmus geclustert um sie in Beobachtungen zu verarbeiten.
In der Lernphase wird mit diesen Beobachtungen pro Übung ein Hidden Markov Model erlernt.
In der folgenden Detektionsphase werden die empfangenen Daten ebenfalls geclustert und die Beobachtungen an alle Hidden Markov Modelle weitergegeben.
Das Hidden Markov Modell, welches die höchste Wahrscheinlichkeit für die Emittierung der beobachteten Folge bestimmt, gilt als Erkenner und die zugehörige Übung wird als ausgeführt behandelt.

## Installation

Mit dem Packetmanager [pip](https://pip.pypa.io/en/stable/) können alle Bibliotheken installiert werden.

```bash
pip install -r requirements.txt
```

## Usage

```
# (in main.py den richtigen Pfad für den Arduino eingeben)
python main.py
# danach den Anweisungen folgen
```

Die einzelnen in der Arbeit besprochenen Parameter können in 'main.py' bearbeitet werden.

## Übersicht
### main.py
Hier findet sich die oberste Ebene der Steuerungslogik, außerdem können hier Parameter angepasst werden.
### my_predictor.py
Hier ist der eigentliche "Lerner" zu finden, der die Hidden Markov Modelle und den K-Means aus übergebenen Daten anlernt.
### arduino_converter.py
Die Daten die vom Arduino gesendet werden müssen in eine besser nutzbare Form gebracht werden, dies wird hier gesammelt getan.
Außerdem findet sich hier die Funktion zum tatsächlichen Lesen.
### pretty_prints.py
Beinhält die Funktionen zur Interaktion mit dem Nutzer, vor allem geht es um die Ausgabe von Anweisungen und das Annehmen der Nutzerantworten.
