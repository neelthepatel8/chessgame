"use client";
import React, { useEffect, useState } from "react";
import Row from "./Row";
import * as fen from "@/app/utils/fenString/fenString";
import { PIECE_COLOR } from "@/app/constants/constants";
import { useWebSocket } from "@/app/services/WebSocketContext";
import { WEBSOCKET } from "@/app/services/constants";
import coordsToAlgebraic from "@/app/utils/coordsToAlgebraic";

import useSound from "use-sound";
import { algebraicToCoords } from "@/app/utils/algebraicToCoords";

const rows = [1, 2, 3, 4, 5, 6, 7, 8].reverse();

const Board = () => {
  const [config, setConfig] = useState({});
  const [currentFen, setCurrentFen] = useState("");
  const [selectedSquare, setSelectedSquare] = useState([]);

  const { sendMessage, messages, isConnected } = useWebSocket();

  const [currentPlayer, setCurrentPlayer] = useState(
    fen.getCurrentPlayer(currentFen),
  );

  const [possibleMoves, setPossibleMoves] = useState([]);

  const [currentMoving, setCurrentMoving] = useState([[], []]);
  const [rookMoving, setRookMoving] = useState([]);

  const [showPromotionOptions, setShowPromotionOptions] = useState([
    [],
    PIECE_COLOR.BLACK,
  ]);
  const [selectedPromotion, setSelectedPromotion] = useState({});

  // Sound Effects:
  const [playMove] = useSound("sfx/move.mp3", { volume: 1 });
  const [playMoveCheck] = useSound("sfx/move.mp3", { volume: 5 });
  const [playCapture] = useSound("sfx/capture.mp3", { volume: 1 });
  const [playCaptureCheck] = useSound("sfx/capture.mp3", { volume: 5 });
  const [playCheck] = useSound("sfx/check.mp3", { volume: 1 });
  const [playCheckmate] = useSound("sfx/checkmate.mp3", { volume: 1 });
  const [playStalemate] = useSound("sfx/stalemate.mp3", { volume: 1 });
  const [playPromotion] = useSound("sfx/promotion.mp3", { volume: 1 });

  useEffect(() => {
    if (isConnected) {
      const initMessage = {
        type: WEBSOCKET.TYPES.INIT,
      };
      sendMessage(initMessage);

      const configurationMessage = {
        type: WEBSOCKET.TYPES.CONFIG,
      };

      sendMessage(configurationMessage);
    }
  }, [isConnected]);

  useEffect(() => {
    const handleWebSockMessaging = async () => {
      const latestMessage = messages[messages.length - 1];
      if (latestMessage) {
        console.log("Recieved message: ", latestMessage);

        if (latestMessage.error < 0) {
          console.log("Recieved error from backend: ", latestMessage);
          return;
        }

        switch (latestMessage.type) {
          case WEBSOCKET.TYPES.INIT:
            const newFen = latestMessage.data?.fen;
            setCurrentFen(newFen);
            setCurrentPlayer(fen.getCurrentPlayer(newFen));
            setPossibleMoves([]);
            setSelectedSquare([]);

          case WEBSOCKET.TYPES.CONFIG:
            setConfig(latestMessage.data?.constants);

          case WEBSOCKET.TYPES.MAKE_MOVE:
            if (latestMessage.data?.move_success == true) {
              const special = latestMessage.data?.special;
              await animateMove(
                latestMessage.data?.fen,
                latestMessage.data?.is_kill == config.KILL,
                special == config.CHECK || special == config.CASTLED_CHECK,
                special == config.PROMOTE_POSSIBLE,
                special == config.CASTLED_CHECK ||
                  special == config.CASTLED_NO_CHECK,
              ).then(() => {
                if (special == config.CHECKMATE) {
                  handleCheckmate();
                } else if (special == config.STALEMATE) {
                  handleStalemate(latestMessage.data?.fen);
                }
              });
            } else {
            }
            setPossibleMoves([]);
            setSelectedSquare([]);
            break;

          case WEBSOCKET.TYPES.POSSIBLE_MOVES:
            const possibleMoves = latestMessage.data?.possible_moves;
            setPossibleMoves(possibleMoves);
            break;

          case WEBSOCKET.TYPES.PROMOTE_PAWN:
            const updatedFen = latestMessage.data?.fen;
            const isCheckmate =
              latestMessage.data?.special === config.CHECKMATE;
            const isStalemate =
              latestMessage.data?.special === config.STALEMATE;
            const isCheck = latestMessage.data?.special === config.CHECK;

            if (isCheckmate) handleCheckmate();
            else if (isStalemate) handleCheckmate();
            else if (isCheck) handleCheck();

            setCurrentFen(updatedFen);

            setCurrentPlayer(fen.getCurrentPlayer(updatedFen));
            setPossibleMoves([]);
            setSelectedSquare([]);
            setShowPromotionOptions([[], PIECE_COLOR.BLACK]);
            setSelectedPromotion([]);
            setCurrentMoving([[], []]);

          default:
            break;
        }
      }
    };

    handleWebSockMessaging();
  }, [messages]);

  useEffect(() => {
    if (showPromotionOptions[0].length > 0) playPromotion();
  }, [showPromotionOptions]);

  useEffect(() => {
    if (selectedPromotion?.type) {
      wsPromotePawn(showPromotionOptions[0]);
    }
  }, [selectedPromotion]);

  const handleCheckmate = async () => {
    const king = document.querySelector(
      `.king-${fen.getCurrentPlayer(currentFen) == PIECE_COLOR.BLACK ? "white" : "black"}`,
    );

    setTimeout(() => {
      playCheckmate();
      const kingSquare = king.parentElement;
      flickerSquare(
        kingSquare,
        8,
        300,
        kingSquare.classList.contains("bg-squarewhite"),
      );
    }, 200);
  };
  const handleStalemate = async (fenStr = currentFen) => {
    const blackKingLocation = fen.getKingLocationFromFen(
      fenStr,
      PIECE_COLOR.BLACK,
    );
    const whiteKingLocation = fen.getKingLocationFromFen(
      fenStr,
      PIECE_COLOR.WHITE,
    );
    const blackKingSquare = document.getElementById(
      `square-${blackKingLocation}`,
    );
    const whiteKingSquare = document.getElementById(
      `square-${whiteKingLocation}`,
    );

    console.log(blackKingSquare, whiteKingSquare);
    setTimeout(() => {
      playStalemate();
      flickerSquare(
        blackKingSquare,
        8,
        300,
        blackKingSquare.classList.contains("bg-squarewhite"),
        true,
      );
      flickerSquare(
        whiteKingSquare,
        8,
        300,
        whiteKingSquare.classList.contains("bg-squarewhite"),
        true,
      );
    }, 300);
  };

  const handleCheck = () => {
    const king = document.querySelector(
      `.king-${fen.getCurrentPlayer(currentFen) == PIECE_COLOR.WHITE ? "white" : "black"}`,
    );
    setTimeout(() => {
      playCheck();
      const kingSquare = king.parentElement;

      flickerSquare(
        kingSquare,
        2,
        300,
        kingSquare.classList.contains("bg-squarewhite"),
      );
    }, 200);
  };

  const animateMove = async (
    newFen,
    isKill = false,
    isCheck = false,
    isPromote = false,
    isCastle = false,
    movingRook = false,
  ) => {
    console.log("rook moving: ", rookMoving);
    const [from_rank, from_file] = movingRook
      ? rookMoving[0]
      : currentMoving[0];
    const [to_rank, to_file] = movingRook ? rookMoving[1] : currentMoving[1];

    const fromSquare = document.getElementById(
      `square-${coordsToAlgebraic(from_rank, from_file)}`,
    );
    const toSquare = document.getElementById(
      `square-${coordsToAlgebraic(to_rank, to_file)}`,
    );
    const piece = fromSquare?.querySelector(".chess-piece");

    console.log("Square from: ", coordsToAlgebraic(from_rank, from_file));
    console.log("Square to: ", coordsToAlgebraic(to_rank, to_file));
    console.log("Piece ", piece);

    if (piece && fromSquare && toSquare) {
      const fromRect = fromSquare.getBoundingClientRect();
      const toRect = toSquare.getBoundingClientRect();
      const transformX = toRect.left - fromRect.left;
      const transformY = toRect.top - fromRect.top;

      const king = document.querySelector(
        `.king-${fen.getCurrentPlayer(currentFen) == PIECE_COLOR.BLACK ? "white" : "black"}`,
      );

      piece.style.position = "relative";
      piece.style.zIndex = 1000;
      piece.style.transform = `translate3d(${transformX}px, ${transformY}px, 0)`;

      function handleMoveOutcome() {
        const executeMoveLogic = () => {
          if (isPromote) {
            setShowPromotionOptions([currentMoving[1], currentPlayer]);
            return;
          }

          if (isKill) {
            isCheck ? playCaptureCheck() : playCapture();
          } else if (isCheck) {
            playMoveCheck();
            if (king) {
              setTimeout(playCheck, 200);
              const kingSquare = king.parentElement;
              flickerSquare(
                kingSquare,
                2,
                300,
                kingSquare.classList.contains("bg-squarewhite"),
              );
            }
          } else {
            playMove();
          }
        };

        if (!movingRook) {
          setTimeout(executeMoveLogic, 200);
        }
      }

      handleMoveOutcome();

      if (movingRook) {
        setTimeout(() => {
          playMove();
        }, 400);
      }

      setTimeout(async () => {
        if (isCastle) {
          await animateMove(newFen, false, false, false, false, true);
        } else {
          setCurrentFen(newFen);
          setCurrentPlayer(fen.getCurrentPlayer(newFen));
          setCurrentMoving([[], []]);
          setRookMoving([[], []]);
          piece.style.transform = "";
          piece.style.zIndex = "";
        }
      }, 500);

      return true;
    }

    return false;
  };

  const flickerSquare = (
    element,
    times,
    interval,
    white = true,
    stalemate = false,
  ) => {
    const classOn = stalemate ? "#89CFF0" : white ? "#EB896F" : "#E2553E";
    const classOff = stalemate ? "#D3D3D3" : white ? "#eeeed2" : "#769656";

    element.style.background = classOff;
    let isOn = false;

    const flicker = () => {
      isOn = !isOn;
      element.style.background = isOn ? classOn : classOff;

      if (times <= 0) {
        element.style.background = classOff;
        return;
      }

      times -= 1;
      setTimeout(flicker, interval);
    };

    flicker();
  };

  const wsShowPossibleMoves = (rank, file) => {
    const message = {
      type: WEBSOCKET.TYPES.POSSIBLE_MOVES,
      data: {
        position: coordsToAlgebraic(rank, file),
      },
    };
    sendMessage(message);
  };

  const wsMovePiece = (from_pos, to_pos) => {
    setCurrentMoving([from_pos, to_pos]);

    const message = {
      type: WEBSOCKET.TYPES.MAKE_MOVE,
      data: {
        from_position: coordsToAlgebraic(from_pos[0], from_pos[1]),
        to_position: coordsToAlgebraic(to_pos[0], to_pos[1]),
      },
    };
    sendMessage(message);
  };

  const wsPromotePawn = (at_pos) => {
    const message = {
      type: WEBSOCKET.TYPES.PROMOTE_PAWN,
      data: {
        position: coordsToAlgebraic(at_pos[0], at_pos[1]),
        promote_to: selectedPromotion?.type,
      },
    };

    sendMessage(message);
  };
  const handleSquareClick = (rank, file, hasPiece, pieceColor) => {
    if (hasPiece) {
      if (
        selectedSquare[0] === rank &&
        selectedSquare[1] === file &&
        pieceColor == currentPlayer
      ) {
        setSelectedSquare([]);
        setPossibleMoves([]);
      } else if (
        selectedSquare.length > 0 &&
        fen.getSquarePieceColor(
          currentFen,
          selectedSquare[0],
          selectedSquare[1],
        ) != pieceColor
      ) {
        wsMovePiece(selectedSquare, [rank, file]);
      } else {
        if (pieceColor == currentPlayer) {
          setSelectedSquare([rank, file]);
          wsShowPossibleMoves(rank, file);
        }
      }
    } else {
      if (selectedSquare.length > 0) {
        const moving_from = coordsToAlgebraic(
          selectedSquare[0],
          selectedSquare[1],
        );

        const piece_name = fen.getPieceAt(currentFen, moving_from);
        console.log("Piece king? ", piece_name, currentFen, moving_from);
        if (piece_name?.toLowerCase() === "k") {
          if (Math.abs(file - selectedSquare[1]) > 1) {
            if (moving_from == "e1") {
              setRookMoving([
                algebraicToCoords(file > selectedSquare[1] ? "h1" : "a1"),
                algebraicToCoords(file > selectedSquare[1] ? "f1" : "d1"),
              ]);
            } else if (moving_from == "e8") {
              setRookMoving([
                algebraicToCoords(file > selectedSquare[1] ? "h8" : "a8"),
                algebraicToCoords(file > selectedSquare[1] ? "f8" : "d8"),
              ]);
            }
          }
        }
        wsMovePiece(selectedSquare, [rank, file]);
      }
    }
  };

  const generatePromotionOptions = () => {
    const options = [];
    const allowedPieceNames = ["queen", "rook", "knight", "bishop"];
    allowedPieceNames.forEach((piece) => {
      options.push({
        type: piece,
        color: showPromotionOptions[1],
      });
    });
    return options;
  };

  return (
    <div className="flex flex-col overflow-hidden rounded-md drop-shadow-2xl">
      {rows.map((row) => (
        <Row
          possibleMoves={possibleMoves}
          selectedSquare={selectedSquare}
          handleSquareClick={handleSquareClick}
          rowFenString={fen.getRow(currentFen, row)}
          key={`row${row}`}
          index={row}
          showPromotionOptions={showPromotionOptions}
          promotionOptions={generatePromotionOptions()}
          setSelectedPromotion={setSelectedPromotion}
        />
      ))}
    </div>
  );
};

export default Board;
