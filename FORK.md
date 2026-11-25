# Fork van Milenco

Persoonlijke fork van [distante/ha-xplora-watch](https://github.com/distante/ha-xplora-watch) (v1.6.0). Releases van deze fork worden via HACS als custom repository geïnstalleerd. Deze wijzigingen worden niet upstream aangeboden.

Branch: `milenco` (standaardbranch van de fork). `main` is ongewijzigd van upstream.

## Wat er extra in zit

| Wat | Toelichting |
|---|---|
| Inloggen als webclient | Inlogoptie `web_client` (standaard aan). Xplora staat één sessie per clienttype toe: als `WEB` (zoals goplay.myxplora.com) draait Home Assistant naast de telefoon-app, die dus ingelogd blijft. Getest op 2026-11-13 met een Guardian-account: deviceList, watchLastLocate, notifications, chatsNew en askWatchLocate werken. Landcode en nummer gaan als cijfers mee (`31`, nummer zonder 0). Bestaande entries zonder de optie loggen in als app. |
| `xplora_watch.refresh_location` | Lichte verversing: alleen de laatst opgeslagen positie, batterij en laden (`watchLastLocate`, één verzoek per horloge). Wekt het horloge niet. `xplora_watch.see` vraagt het horloge nog steeds om een nieuwe positie. |
| Optie `max_accuracy` | Posities die minder nauwkeurig zijn dan dit aantal meters (zendmast/LBS) verplaatsen de tracker niet; de genegeerde positie staat in het attribuut `ignored_fix`. 0 = uit. |
| Optie `media_retention_hours` | Spraak, foto's en video's uit de chat staan onder `config/www` (zonder inlog op te vragen als je de bestandsnaam kent). Met een waarde boven 0 verwijdert `read_message` oudere bestanden en downloadt het media van oudere berichten niet opnieuw; de chatkaart toont ze dan als niet beschikbaar. De foto van het horloge zelf blijft. 0 = altijd bewaren. |
| Zonemeldingen uit de feed | Event `xplora_watch_safezone` bij ARRIVE/LEAVE_SAFE_ZONE (commit uit de branch bij upstream-issue #17), aangevuld met de zonenaam (`zone`, uit `safezone_name`), `zone_id`, `addr` en `rad` zoals een echte feedregel ze bevat. |
| Chatkaart: geen dubbele berichten | Een bericht waarvan de media niet (meer) te laden is, wordt bij elke update opnieuw opgebouwd. Upstream bleef de oude versie daarbij staan, onder het nieuwste bericht, en kwam er bij elke update een kopie bij. Met `media_retention_hours` gold dat voor bijna alle spraakberichten. |

Tests van de fork staan in `tests/xplora_watch/fork/`, die van de kaarten in `tests/card/` (`npm ci`, dan `npx vitest run`).

## Nieuwe release maken

```bash
scripts/fork-release.sh v1.6.0-milenco.2 "Wat er veranderd is"
```

Het script zet de versie in `manifest.json`, commit en tagt die, pusht naar `fork` en maakt een GitHub-release. Releases niet als pre-release markeren: HACS toont die alleen met bèta aan.

## Testen

```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements.txt   # runtime
# testpakketten: de versies uit requirements-test-lock.txt (op macOS zonder --require-hashes)
.venv/bin/python -m pytest -q --no-cov --timeout 30
.venv/bin/ruff check custom_components tests && .venv/bin/ruff format --check custom_components tests
.venv/bin/mypy custom_components/xplora_watch
```

## Upstream bijhouden

```bash
git fetch origin --tags
git merge <nieuwe-upstream-tag>
```
