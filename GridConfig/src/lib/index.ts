// place files you want to import through the `$lib` alias in this folder.
export enum CellType {
	Wall,
	Entrance,
	Exit,
	StudyTable,
	Chair
}

export interface BaseCell {
	type: CellType;
}

export interface EntranceCell extends BaseCell {
	type: CellType.Entrance;
	associatedExit: [number, number]; // Coordinate pair for the exit
}

export interface NonEntranceCell extends BaseCell {
	type: Exclude<CellType, CellType.Entrance>;
	associatedExit: null;
}

// Union type for all cells
export type Cell = EntranceCell | NonEntranceCell;

export function colorForCell(cell: CellType): string {
	switch (cell) {
		case CellType.Wall:
			return 'red';
		case CellType.Entrance:
			return 'blue';
		case CellType.Exit:
			return 'green';
		case CellType.StudyTable:
			return 'gray';
		case CellType.Chair:
			return 'purple';
	}
}
