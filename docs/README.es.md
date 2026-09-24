# jev-olympics

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · **Español** · [한국어](README.ko.md)

Let Jev do math, chat, and draw things—in a probabilistic way.

Deja que Jev calcule, converse y dibuje de forma probabilística. [Probar en línea](https://jev-olympics.vercel.app/)

## Funciones

- **Calculator:** selecciona dígitos desde las unidades con Choice o busca un entero mediante las decisiones «igual / mayor / menor» de Noul. Compara la predicción con el resultado aritmético exacto.
- **Chat:** construye respuestas en inglés carácter a carácter o palabra a palabra. El modo de palabras ofrece 249 palabras comunes, `. , ? !`, salto de línea y fin: 255 opciones. Los espacios se insertan automáticamente.
- **Canvas:** dibuja en una cuadrícula en blanco y negro, de 4×4 a 14×14, recorriendo píxeles, eligiendo coordenadas o moviendo un bolígrafo.
- **Notes:** añade instrucciones compartidas o palabras de ánimo a cada decisión. Tienen prioridad sobre las instrucciones integradas, dentro de las opciones disponibles.

Haz clic en un dígito, carácter, palabra o decisión de dibujo para ver las probabilidades, confidence (si está disponible), modelo, tiempo y tokens. «Ver entrada completa» está plegado por defecto y muestra el JSON real sin credenciales. Las predicciones no se corrigen. La interfaz admite seis idiomas; cambiar el idioma no traduce las instrucciones ni las respuestas del modelo. Al recargar se borran la conversación, el dibujo, Notes y las claves personales.

## Clave compartida y BYOK

El sitio público usa una clave del servidor por defecto: puedes probarlo sin introducir una. El botón superior permite usar tu propia clave TypeSafe, que tendrá prioridad. Al borrarla vuelves a la compartida. Si se rechaza tu clave, nunca se usa automáticamente la cuota del propietario.

Obtén una clave en la [consola de TypeSafe](https://console.typesafe.ai/keys). Tu clave permanece solo en la memoria de la página y se envía por HTTPS al backend. La clave compartida nunca se envía al navegador.

## Ejecución local

Necesitas Python 3.9 o posterior. El modo TypeSafe no requiere dependencias adicionales. Desde la raíz del proyecto:

```bash
python3 calculator.py
```

Abre <http://127.0.0.1:8765>. Usa `--port 8766` para cambiar el puerto. El modelo predeterminado es `jev-1.13.0`.

Puedes configurar `TYPESAFE_API_KEY` en `.env`. La prioridad local es: entorno del proceso → `.env` → clave del navegador. Reinicia tras cambiar la clave de entorno. A diferencia del sitio público, la clave local de entorno tiene prioridad sobre la personal. Nunca incluyas claves reales en Git.

## Despliegue en Vercel

Añade `TYPESAFE_API_KEY` como **Secret** para **Production** y vuelve a desplegar:

```bash
vercel env add TYPESAFE_API_KEY production --sensitive
vercel deploy --prod
```

Introduce la clave cuando lo pida la CLI; no la pongas en argumentos ni en el código. Solo se activa con `VERCEL_ENV=production`. Los despliegues de vista previa siguen exigiendo BYOK. La nube no carga `.env` ni los pesos locales de Laya. Elimina la variable y vuelve a desplegar para desactivar el acceso compartido.

El uso público consume la cuota TypeSafe del propietario, que la administra desde la consola. La aplicación no tiene un límite de gasto ni de solicitudes distribuido entre instancias. La comprobación del origen no impide llamadas directas mediante scripts.

## Límites y desarrollo

El modo de caracteres se detiene tras dos espacios consecutivos o cinco caracteres idénticos. El de palabras se detiene tras cinco selecciones idénticas. Los límites son 64 / 128 / 256 caracteres o 32 / 64 / 128 decisiones en modo de palabras. Las paradas por límite o repetición se marcan como incompletas; no se inventa un `END`. El dibujo también respeta límites de cuadrícula, repetición y pasos, conservando el resultado parcial.

Las pruebas están en `tests/` y no llaman a la API de pago:

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m unittest tests.test_chat_words -v
```

`calculator_ui/` contiene la interfaz, `api/` las funciones de nube y `docs/` las traducciones. Laya local es opcional, no necesita clave y no recurre a la nube si falla. Consulta el [README en inglés](../README.md) para los algoritmos, la instalación de Laya y la estructura completa.
