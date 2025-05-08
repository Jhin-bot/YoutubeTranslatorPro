import os
import re
from setuptools import setup, find_packages

# Get package version
VERSION = '1.0.0'

# Read long description from README.md
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = f.read().splitlines()

setup(
    name='youtube-transcriber-pro',
    version=VERSION,
    author='YouTubeTranscriberPro Team',
    author_email='info@ytpro.example.com',
    description='Transcribe, translate, and process YouTube videos using Whisper',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/username/YouTubeTranscriberPro',
    project_urls={
        'Bug Tracker': 'https://github.com/username/YouTubeTranscriberPro/issues',
        'Documentation': 'https://github.com/username/YouTubeTranscriberPro#readme',
        'Source Code': 'https://github.com/username/YouTubeTranscriberPro',
    },
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'YouTubeTranscriberPro': ['*.json', '*.png', '*.ico', '*.md'],
    },
    python_requires='>=3.8',
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'yttrans=YouTubeTranscriberPro.main:main',
        ],
        'gui_scripts': [
            'yttrans-gui=YouTubeTranscriberPro.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Topic :: Multimedia :: Sound/Audio :: Speech',
        'Topic :: Multimedia :: Video',
        'Topic :: Utilities',
        'Environment :: X11 Applications :: Qt',
        'Environment :: Win32 (MS Windows)',
        'Environment :: MacOS X',
    ],
    keywords='youtube transcription translation whisper openai subtitles srt',
    zip_safe=False,
    platforms=['any'],
)
