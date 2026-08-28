# Instrukcje wykonawcze dla Codexa

- Codex realizuje wyłącznie jawnie wskazany Task.
- Źródłem treści Tasków jest katalog `docs/tasks/`.
- Sama obecność pliku w `docs/tasks/` nie oznacza zgody na jego wykonanie.
- Codex rozpoczyna Task wyłącznie po bezpośrednim poleceniu użytkownika wskazującym konkretny `TASK-xxx`.
- Codex nie rozpoczyna automatycznie kolejnego Tasku po zakończeniu bieżącego.
- W przypadku konfliktu, niejednoznaczności lub potrzeby zmiany Core Codex stosuje zasadę STOP i raportuje problem.
- Codex nie zmienia zatwierdzonych decyzji architektonicznych ani biznesowych.
- Każdy Task kończy raportem w formacie wymaganym przez dany Task.
- Codex pracuje wyłącznie w bieżącym repozytorium, chyba że Task jawnie stanowi inaczej.
