"""Testmodule for project1developers.py"""
import unittest
import os
import csv
from unittest.mock import patch, Mock
import pandas as pd
import project1developers as p1d

class TestTestProject1Developers(unittest.TestCase):
    """Test suite for the project1developers module.
    This class contains unit tests for the project1developers module"""

    @classmethod
    def setUpClass(cls):
        os.makedirs("project1devs", exist_ok=True)

    @patch("project1developers.Repository")
    def test_get_developers_from_repo(self, mock_repo_class):
        """Tests get_developers with test data"""

        commit1 = Mock()
        commit1.author.name = "Maija"
        commit1.author.email = "maija@meikalainen.com"
        commit1.committer.name = "Erkki Esimerkki"
        commit1.committer.email = "erkki.esimerkki@kuukkel.com"

        commit2 = Mock()
        commit2.author.name = "Erkki Taas"
        commit2.author.email = "erkki.esimerkki@kuukel.com"
        commit2.committer.name = "Tiina Tossavainen"
        commit2.committer.email = "tiinat@yritys.fi"

        mock_repo = Mock()
        mock_repo.traverse_commits.return_value = [commit1, commit2]
        mock_repo_class.return_value = mock_repo

        result = p1d.get_developers_from_repo("wrong_url")
        expected = sorted([
            ("Maija", "maija@meikalainen.com"),
            ("Erkki Esimerkki", "erkki.esimerkki@kuukkel.com"),
            ("Erkki Taas", "erkki.esimerkki@kuukel.com"),
            ("Tiina Tossavainen", "tiinat@yritys.fi"),
        ])
        self.assertEqual(result, expected)

    @patch("project1developers.Repository")
    def test_get_developers_empty_repo(self, mock_repo):
        """Test that get_developers_from_repo returns an empty list 
            when the repository raises an exception."""
        mock_repo.return_value.__iter__.side_effect = Exception("repo failed")

        result = p1d.get_developers_from_repo("fake_url")

        # If an error occurs, an empty list is returned.
        self.assertEqual(result, [])

    @patch("project1developers.logging")
    @patch("project1developers.Repository")
    def test_get_developers_from_repo_invalid_url(self, mock_repo_class, mock_logging):
        """Test that get_developers_from_repo() handles invalid repo URL."""

        # Defines the mock so that when the Repository is called, it throws an exception.
        mock_repo_class.side_effect = Exception("Invalid repository URL")

        result = p1d.get_developers_from_repo("https://github.com/doesntexist/url")

        # check that logging.error was called with some argument
        mock_logging.error.assert_called()
        self.assertEqual(result, [])

    def test_project_folder_exists(self):
        """Check that project1devs directory exists."""
        self.assertTrue(os.path.isdir("project1devs"))

    def test_save_developers_to_csv(self):
        """Test that save_developers_to_csv creates a CSV file with correct header"""

        devs = [("Erkki Esimerkki", "erkki@esimerkki.fi")]
        outputfile = "testfile"

        p1d.save_developers_to_csv(devs, outputfile)

        path = os.path.join("project1devs", f"{outputfile}.csv")
        self.assertTrue(os.path.exists(path))

        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        self.assertEqual(rows[0], ["name", "email"])

    def test_read_developers(self):
        """Test that read_developers reads saved data correctly."""

        outputfile = "test_read"
        path = os.path.join("project1devs", f"{outputfile}.csv")

        # creating small testfile
        with open(path, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["name", "email"])
            writer.writerow(["Erkki Esimerkki", "erkki@esimerkki.com"])

        result = p1d.read_developers(outputfile)

        self.assertEqual(result, [["Erkki Esimerkki", "erkki@esimerkki.com"]])

    def test_process(self):
        """Test that process() correctly extracts name, initials, and email prefix."""
        dev = ["Êrkkä ASImèrkki", "erkka.esimerkki@yritys.com"]
        result = p1d.process(dev)

        expected = (
            "erkka asimerkki",              # name
            "erkka",                        # firstname
            "asimerkki",                    # lastname
            "e",                            # firstname initial
            "a",                            # lastname initial
            "erkka.esimerkki@yritys.com",   # email
            "erkka.esimerkki"               # email prefix
        )

        self.assertEqual(result, expected)

    def test_process_single_word_name(self):
        """Test process() with a single word name."""
        dev = ["Erkki", "erkkiesimerkki@yritys.com"]
        result = p1d.process(dev)

        expected = (
            "erkki",                        # name
            "erkki",                        # firstname
            "",                             # lastname
            "e",                            # firstname initial
            "",                             # lastname initial
            "erkkiesimerkki@yritys.com",    # email
            "erkkiesimerkki"                # email prefix
        )

        self.assertEqual(result, expected)

    def test_process_multiple_words_name(self):
        """Test that process() correctly handles a name with more than two words."""
        dev = ["Vaka Vanha Väinämöinen", "vaka@vanha.com"]
        result = p1d.process(dev)

        expected = (
            "vaka vanha vainamoinen",   # normalized name
            "vaka",                     # first name
            "vanha vainamoinen",        # last name (everything after first)
            "v",                        # first initial
            "v",                        # last initial
            "vaka@vanha.com",           # email
            "vaka"                      # email prefix
        )

        self.assertEqual(result, expected)

    def test_compute_similarity(self):
        """Test that compute_similarity returns a list for two developers."""
        devs = [
            ["Erkki Esimerkki", "erkki.esimerkki@yritys.fi"],
            ["Erkka Esim", "erkki@sampleesimerkki.com"]
        ]
        result = p1d.compute_similarity(devs)
        #Expect a list of length 1 (only one pair)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        # Check that pair has the right names
        self.assertEqual(result[0][0], "Erkki Esimerkki")
        self.assertEqual(result[0][2], "Erkka Esim")

    def test_compute_similarity_empty_lastname(self):
        """Test that compute_similarity handles empty last names corretly."""
        devs = [
            ["Erkki", "erkki@esimerkki.com"],
            ["Erkki", "erkki@virtanen.com"]
        ]
        result = p1d.compute_similarity(devs)
        # c32 (lastname similarity) should be 0.0
        self.assertEqual(result[0][7], 0.0)

    def test_compute_similarity_all_conditions(self):
        """Test compute_similarity conditions."""
        devs = [
            ["Erkki Esimerkki", "erkki.esimerkki@yritys.com"],
            ["E Esim", "e.esim@firma.fi"]
        ]

        result = p1d.compute_similarity(devs)

        self.assertEqual(len(result), 1)
        pair = result[0]

        self.assertGreaterEqual(pair[4], 0.0)  # c1
        self.assertGreaterEqual(pair[5], 0.0)  # c2
        self.assertGreaterEqual(pair[6], 0.0)  # c3.1
        self.assertGreaterEqual(pair[7], 0.0)  # c3.2

        self.assertIsInstance(pair[8], bool)  # c4
        self.assertIsInstance(pair[9], bool)  # c5
        self.assertIsInstance(pair[10], bool) # c6
        self.assertIsInstance(pair[11], bool) # c7

    def test_filter_similarity(self):
        """Test filter_similarity keeps rows meeting threshold conditions."""
        testdata = {
            "name_1": ["Max", "Max"],
            "email_1": ["max@yritys.com", "max@firma.com"],
            "name_2": ["Max", "Pentti"],
            "email_2": ["max@yritys.com", "pentti.virtanen@osoite.fi"],
            "c1": [1.0, 0.0],       
            "c2": [1.0, 0.2],       
            "c3.1": [1.0, 0.4],
            "c3.2": [1.0, 0.4],
            "c4": [False, False],
            "c5": [False, False],
            "c6": [False, False],
            "c7": [False, False],
        }
        df = pd.DataFrame(testdata)

        # You can adjust threshold value here
        t= 0.7

        df_filtered = p1d.filter_similarity(df, t)

        expected_rows = df[
        (df["c1"] >= t) | (df["c2"] >= t) |
        ((df["c3.1"] >= t) & (df["c3.2"] >= t)) |
        df[["c4", "c5", "c6", "c7"]].any(axis=1)
        ]

        # Check the results in the file below
        df_filtered.to_csv("test_result_filter_similarity.csv", index=False)

        pd.testing.assert_frame_equal(df_filtered.reset_index(drop=True),
                                  expected_rows.reset_index(drop=True))

    def test_save_similarity_df(self):
        """Test for save_similarity_df."""
        df = pd.DataFrame({
            "name_1": ["Erkki"],
            "email_1": ["erkki@esimerkki.com"],
            "name_2": ["Väinö"],
            "email_2": ["vaka@vainamoinen.com"],
            "c1": [0.3], "c2": [0.3], "c3.1": [0], "c3.2": [0],
            "c4": [False], "c5": [False], "c6": [False], "c7": [False]
        })
        p1d.save_similarity_df(df, t=0.7, outputfile="test")
        self.assertTrue(os.path.exists("project1devs/test_similarity_t=0.7.csv"))

if __name__ == "__main__":
    unittest.main()
