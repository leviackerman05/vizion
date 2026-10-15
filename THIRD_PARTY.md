# Third-party components

Vizion uses Manim Community (MIT), FastAPI (MIT), SQLAlchemy (MIT), React (MIT), and FFmpeg (its distribution's LGPL/GPL build terms). Their licenses and notices remain in the installed distributions. The original repositories' history is preserved; archived code is not part of the runtime.

Offline narration uses [Piper](https://github.com/OHF-Voice/piper1-gpl), GPL-3.0. The unmodified Piper package is invoked as a separate CLI process. Its source and license are available from that upstream repository and its package source distribution. Preserve the applicable license/source obligations when distributing container images or binaries. This note does not replace dependency license texts.

The selected voice is `en_US-ljspeech-high`. Its [model card](https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/ljspeech/high/MODEL_CARD) identifies the [LJ Speech dataset](https://keithito.com/LJ-Speech-Dataset/) as public domain and says this voice was trained from scratch. The app deliberately avoids the Lessac voice whose dataset is restricted to non-commercial use. Voice files are downloaded from the Piper voice repository during image build, not committed here.

Groq hosts the configured GPT OSS model under its own service agreement and quota. Vizion sends lesson topic, audience, and storyboard validation feedback to that provider. Narration and Manim rendering run locally on the worker. No provider credentials are embedded in the browser bundle.
