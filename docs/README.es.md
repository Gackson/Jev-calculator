# jev-olympics

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · **Español** · [한국어](README.ko.md)

Let Jev do math, chat, and draw things—in a probabilistic way.

[Entrar en la arena](https://jev-olympics.vercel.app/)

Tres pruebas. Ninguna medalla. Un informe de incidente detallado por cada error.

Un pequeño patio de recreo con el modelo Jev de TypeSafe. En vez de pedirle una respuesta terminada, hacemos que calcule, converse y dibuje tomando una decisión cada vez. Está hecho para divertirse. Cualquier utilidad práctica es un efecto secundario no previsto.

## Las pruebas

- **Calculator:** elige dígitos desde las unidades con Choice o busca un entero con los juicios de igualdad y tamaño de Noul. Al lado hacemos el cálculo real, para que la decepción también sea medible.
- **Chat:** construye una respuesta en inglés carácter a carácter o palabra a palabra. El modo de palabras tiene 249 palabras comunes, `. , ? !`, `NEWLINE` y `END`: 255 opciones. Los espacios se insertan automáticamente.
- **Canvas:** dibuja en una cuadrícula en blanco y negro de 4×4 a 14×14, recorriendo píxeles, eligiendo coordenadas o moviendo un bolígrafo. Que el resultado se parezca a la descripción forma parte del experimento.
- **Notes:** añade instrucciones, contexto o ánimo a cada decisión. Tienen prioridad sobre las instrucciones integradas, dentro de las opciones disponibles.

## Inspeccionar los restos

Haz clic en un dígito, carácter, palabra o decisión de dibujo para ver las probabilidades, confidence cuando esté disponible, modelo, tiempo y tokens. Despliega **Ver entrada completa** para consultar el JSON exacto enviado en ese paso, sin credenciales.

Las predicciones se quedan tal como las hizo Jev. No corregimos el examen después de consultar las soluciones. Calculator señala el primer juicio equivocado; Chat y Canvas conservan el trabajo incompleto.

La interfaz y este README admiten los mismos seis idiomas. Cambiar de idioma no traduce las instrucciones ni las respuestas del modelo. La conversación, el dibujo y Notes viven en la memoria de la página y desaparecen al recargar.

## Reglas del juego

- **Calculator:** admite enteros, operadores aritméticos y paréntesis. La referencia usa aritmética racional exacta; la comparación usa el entero truncado hacia cero. Choice permite 24 dígitos y una comprobación final de terminación. Noul amplía el intervalo y después usa valores aleatorios o puntos medios. Choice puede incluir o excluir las predicciones anteriores del contexto.
- **Chat:** cada paso recibe el mensaje, la respuesta parcial, hasta tres turnos anteriores y Notes. El modo de palabras también recibe las selecciones previas. Dos espacios consecutivos o cinco caracteres idénticos detienen el modo de caracteres; cinco selecciones idénticas detienen el de palabras. Los límites son 64 / 128 / 256 caracteres o 32 / 64 / 128 decisiones en modo de palabras, contando puntuación y marcadores de control. Las paradas por repetición o límite se marcan como incompletas, nunca se disfrazan de `END`.
- **Canvas:** la enumeración recorre los píxeles en orden; Monte Carlo elige coordenadas o `END`; el bolígrafo elige un inicio, una dirección, levantar la punta o `END`. Los bordes, las comprobaciones de repetición y los límites de pasos mantienen finito el experimento.
- **Notes:** se fijan al iniciar la ejecución y se envían sin cambios en cada decisión. No se pueden editar a mitad del proceso. Notes no garantiza mejores predicciones.

## Ejecución local

Python 3.9 o posterior; la inferencia TypeSafe no necesita dependencias Python adicionales. Configura `TYPESAFE_API_KEY` en el entorno o en un archivo `.env` en la raíz del proyecto:

```dotenv
TYPESAFE_API_KEY=your-typesafe-api-key
```

```bash
python3 calculator.py
```

Abre <http://127.0.0.1:8765>. Usa `--port 8766` para cambiar el puerto o `--model jev-latest` para cambiar el modelo. El predeterminado es `jev-1.13.0`. El servidor solo escucha en localhost. Reinicia tras modificar la configuración y no incluyas credenciales reales en Git.

También se admite inferencia local opcional con **Laya**. La instalación, el despliegue y la configuración se explican en la [guía de desarrollo en inglés](development.md).

## Desarrollo

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m unittest tests.test_chat_words -v
node --check calculator_ui/app.js
```

Las pruebas simulan respuestas del modelo; las de integración HTTP usan un puerto de loopback. CI comprueba Python 3.9 y 3.12 y la sintaxis del JavaScript de la interfaz. Verificamos que funcione el experimento, no que Jev haya desarrollado sentido común.

| Directorio | Contenido |
| --- | --- |
| `calculator_ui/` | Interfaz y traducciones |
| `api/` | Puntos de entrada de las funciones Vercel |
| `tests/` | Pruebas unitarias y de integración HTTP |
| `docs/` | READMEs traducidos y guía de desarrollo |

Referencias: [Inicio rápido de TypeSafe](https://docs.typesafe.ai/introduction/quickstart), [Choice](https://docs.typesafe.ai/primitives/choice), [HTTP API](https://docs.typesafe.ai/api), [confidence](https://docs.typesafe.ai/confidence).
