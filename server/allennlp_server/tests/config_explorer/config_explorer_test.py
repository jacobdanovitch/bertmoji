import json

from allennlp.common.testing import AllenNlpTestCase

from allennlp_server.config_explorer import make_app


class TestConfigExplorer(AllenNlpTestCase):
    def setUp(self):
        super().setUp()
        app = make_app()
        app.testing = True
        self.client = app.test_client()

    def test_app(self):
        response = self.client.get("/")
        html = response.get_data().decode("utf-8")

        assert "AllenNLP Configuration Wizard" in html

    def test_api(self):
        response = self.client.get("/api/config/")
        data = json.loads(response.get_data())

        assert data["className"] == ""

        items = data["config"]["items"]

        assert items[0] == {
            "name": "dataset_reader",
            "configurable": True,
            "registrable": True,
            "comment": "specify your dataset reader here",
            "annotation": {"origin": "allennlp.data.dataset_readers.dataset_reader.DatasetReader"},
        }

    def test_choices(self):
        response = self.client.get(
            "/api/config/?class=allennlp.data.dataset_readers.dataset_reader.DatasetReader"
            "&get_choices=true"
        )
        data = json.loads(response.get_data())

        assert "allennlp.data.dataset_readers.snli.SnliReader" in data["choices"]

    def test_subclass(self):
        response = self.client.get(
            "/api/config/?class=allennlp.data.dataset_readers.semantic_role_labeling.SrlReader"
        )
        data = json.loads(response.get_data())

        config = data["config"]
        items = config["items"]
        assert config["type"] == "srl"
        assert items[0]["name"] == "token_indexers"

    def test_instantiable_registrable(self):
        response = self.client.get("/api/config/?class=allennlp.data.vocabulary.Vocabulary")
        data = json.loads(response.get_data())
        assert "config" in data
        assert "choices" not in data

        response = self.client.get(
            "/api/config/?class=allennlp.data.vocabulary.Vocabulary&get_choices=true"
        )
        data = json.loads(response.get_data())
        assert "config" not in data
        assert "choices" in data

    def test_get_choices_failover(self):
        """
        Tests that if we try to get_choices on a non-registrable class
        it just fails back to the config.
        """
        response = self.client.get(
            "/api/config/?class=allennlp.modules.feedforward.FeedForward&get_choices=true"
        )
        data = json.loads(response.get_data())
        assert "config" in data
        assert "choices" not in data

    def test_torch_class(self):
        response = self.client.get(
            "/api/config/?class=allennlp.training.optimizers.RmsPropOptimizer"
        )
        data = json.loads(response.get_data())
        config = data["config"]
        items = config["items"]

        assert config["type"] == "rmsprop"
        assert any(item["name"] == "lr" for item in items)

    def test_rnn_hack(self):
        """
        Behind the scenes, when you try to create a torch RNN,
        it just calls torch.RNNBase with an extra parameter.
        This test is to make sure that works correctly.
        """
        response = self.client.get("/api/config/?class=torch.nn.modules.rnn.LSTM")
        data = json.loads(response.get_data())
        config = data["config"]
        items = config["items"]

        assert config["type"] == "lstm"
        assert any(item["name"] == "batch_first" for item in items)

    def test_initializers(self):
        response = self.client.get(
            "/api/config/?class=allennlp.nn.initializers.Initializer&get_choices=true"
        )
        data = json.loads(response.get_data())

        assert "allennlp.nn.initializers.ConstantInitializer" in data["choices"]
        assert "allennlp.nn.initializers.BlockOrthogonalInitializer" in data["choices"]

        response = self.client.get("/api/config/?class=allennlp.nn.initializers.UniformInitializer")
        data = json.loads(response.get_data())
        config = data["config"]
        items = config["items"]

        assert config["type"] == "uniform"
        assert any(item["name"] == "a" for item in items)

    def test_regularizers(self):
        response = self.client.get(
            "/api/config/?class=allennlp.nn.regularizers.regularizer.Regularizer&get_choices=true"
        )
        data = json.loads(response.get_data())

        assert "allennlp.nn.regularizers.regularizers.L1Regularizer" in data["choices"]

        response = self.client.get(
            "/api/config/?class=allennlp.nn.regularizers.regularizers.L1Regularizer"
        )
        data = json.loads(response.get_data())
        config = data["config"]
        items = config["items"]

        assert config["type"] == "l1"
        assert any(item["name"] == "alpha" for item in items)
