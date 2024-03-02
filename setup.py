from setuptools import setup, find_packages

setup(
    name='your_streamlit_app',
    version='0.1',
    install_requires=[
            "altair",
            "numpy",
            "pandas",
            "pydeck",
            "streamlit",
            "pyproj",
            "bokeh",
            "searoute",
        # Add other dependencies as necessary
    ],
    packages=find_packages(),
)
