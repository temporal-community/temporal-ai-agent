import shared.config


def transfer_control(args: dict) -> dict:
    return {
        "new_goal": shared.config.AGENT_GOAL,
    }
