from sentinel.infrastructure.logger import logger
from sentinel.kernel.bootstrap import Bootstrap


def main() -> None:
    bootstrap = Bootstrap()

    try:
        bootstrap.start()

        logger.info("Sentinel OS started successfully.")

        input("\nPress ENTER to shutdown...")

    finally:
        bootstrap.shutdown()
        logger.info("Sentinel OS shutdown completed.")


if __name__ == "__main__":
    main()