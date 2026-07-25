from sentinel.kernel.bootstrap import Bootstrap


def main() -> None:
    bootstrap = Bootstrap()

    try:
        bootstrap.start()
        print("Sentinel OS started successfully.")

        input("\nPress ENTER to shutdown...")

    except Exception as exc:
        print(f"Failed to start Sentinel OS: {exc}")

    finally:
        try:
            bootstrap.shutdown()
        except RuntimeError:
            # Kernel was never started or is already shut down.
            pass


if __name__ == "__main__":
    main()