from jev_game.main import main


def test_main_runs(capsys):
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "Hello, world!"
