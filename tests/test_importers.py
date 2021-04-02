from choixe.importers import Importer


class TestImporters:

    def test_options(self):

        v = '@import(alpha.yml, beta.yml, delta.yml, default=gamma.yml)'

        importer = Importer.from_string(v)
        assert importer is not None

        print(importer.path)
        print(importer.options)
        print(importer.default_value)
